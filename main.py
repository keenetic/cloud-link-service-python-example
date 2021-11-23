import json
from threading import Thread
from typing import Optional
from flask import Flask, request, jsonify, Response
from functools import wraps

from ndcloudclient.ec import *
from ndcloudclient.ndss import NDSS, NDSSException, KeeneticDeviceException
from record_store import RecordStore


app = Flask(__name__, instance_relative_config=True)

# You can select the way of configuration:
# - json file
# - flask app config

# comment/uncomment next 2 lines to read config from json file
with open('instance/config.json') as f:
    config = json.load(f)

# comment/uncomment next 2 lines to read from flask app config
# app.config.from_pyfile('config.py')
# config = app.config

ndss_service_id = config.get('NDSS_SERVICE_ID')


def get_params_from_config_by_prefix(prefix: str) -> dict[str]:
    """
    Returns parameters from config with names, starting with prefix

    :param prefix: prefix for names to return
    :return: dict of params
    """
    return {str(k): str(v) for k, v in config.items() if str(k).startswith(prefix)}


ndss_client = NDSS(get_params_from_config_by_prefix('NDSS_'))
recordstore_type = config.get('RECORDSTORE')

rs: Optional[RecordStore] = None
if recordstore_type == 'file':
    from record_store_files import RecordStoreFiles
    filestore_prefix = config.get('RECORDSTORE_DIRPREFIX')
    rs = RecordStoreFiles(ndss_service_id, filestore_prefix)
if recordstore_type == 'firestore':
    from record_store_firestore import RecordFirestore
    firestore_project = config.get('FIRESTORE_PROJECT')
    rs = RecordFirestore(ndss_service_id, firestore_project)


def log(message: str) -> None:
    """
    Logs message
    """
    print(message)


def log_request_debug() -> None:
    """
    Outputs some debug information.
    Add call of this method to necessary request handlers
    """
    log("URL=" + request.url)
    if request.data:
        log("DATA=" + str(request.data))


def extract_parameters_from(req: 'request') -> dict[str, str]:
    """
    Extracts GET-parameters from Flask request

    :param req: Flask request
    :return: dict of strings
    """
    return dict(req.args.items())


def contains_all_mandatory(params: dict[str], mandatory: list[str]) -> bool:
    """
    Checks, if given params dict contains all items from mandatory list

    :param params: dict of strings
    :param mandatory: list of strings
    :return: True or False
    """
    return all(m in params.keys() for m in mandatory)


def format_success(text: str) -> 'Response':
    """
    Formats success
    """
    return jsonify({'success': text})


def format_error(code: str, text: str) -> 'Response':
    """
    Formats error
    """
    return jsonify(
        {
            'code': code,
            'error': text
        }
    )


def check_basic_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.get('DEBUG_SKIP_CALLBACK_BASICAUTH'):
            is_callback_authorized = ndss_client.check_callback_auth(request.headers.get('Authorization'))
            if not is_callback_authorized:
                return format_error('0x401', 'authorization failed'), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/ndmp/linkService', methods=['POST'])
@check_basic_auth
def link_service():
    """
    Handles linkService requests from NDSS

    # todo: write more, describe cases when NDSS visits this link
    """
    log_request_debug()

    options = VerifySignatureOptions()
    options.skip_check_timestamp = config.get('DEBUG_SKIP_CHECK_TIMESTAMP')

    params = extract_parameters_from(request)

    are_all_params = contains_all_mandatory(
        params, ['tokenAlias', 'serviceId', 'deviceEcPublic', 'timestamp', 'ecSignature'])
    if not are_all_params:
        return format_error('', 'missing some mandatory params'), 422
    # So, from here, we are safe to call params.get()

    try:
        is_signature_verified = verify_signature_from_dict(params, options)
    except VerifySignatureError:
        is_signature_verified = False

    if is_signature_verified:
        thread = Thread(
            target=do_generate_and_validate,
            kwargs={
                'service_id': params.get('serviceId'),
                'device_ec_public': params.get('deviceEcPublic'),
                'token_alias': params.get('tokenAlias')
            }
        )
        thread.start()

        # Important: This is not the end, our process is being continued in the other thread,
        # see do_generate_and_validate

        # NDSS doesn't care about body content, only status code is important
        return format_success('started validation'), 200  # the signature is verified, but device is not linked yet
    return format_error('', 'signature is not verified'), 422


def do_generate_and_validate(
        service_id: str,
        device_ec_public: str,
        token_alias: str
) -> None:
    """
    This method starts from link_service method in own thread,
    generates EC keys, creates signature and sends it to NDSS.

    And saves data somehow.

    :param service_id:
    :param device_ec_public:
    :param token_alias:
    :return:
    """

    signing_key: 'SigningKey' = generate_ec_keys()
    service_ec_public = get_ec_public_key(signing_key.verifying_key)
    ec_signature, signed_timestamp = \
        sign_ec_signature_for_validate(signing_key, service_id, device_ec_public, service_ec_public)

    # You need to develop your own data structure instead of this primitive
    record = \
        RecordStore.prepare_ec_record(token_alias, get_ec_private_key(signing_key), service_ec_public, device_ec_public)
    rs.save_pending_ec_record(token_alias, record)

    try:
        log(f'Starting validate_link for {token_alias} with {signed_timestamp}')
        ndss_client.validate_link(
            device_ec_public,
            service_ec_public,
            token_alias,
            signed_timestamp,
            ec_signature
        )
    except NDSSException:
        log(f'NDSS Exception during validate_link process for {token_alias}')
        return
    except KeeneticDeviceException as kde:
        log(f'Got {kde.code} while validate_link {token_alias}')
        return

    # if there was no exception during validate_link, save token alias and record data to local storage
    rs.save_active_ec_record(token_alias, record)
    log(f'Successfully linked {token_alias}')


@app.route('/search', methods=['GET'])
@check_basic_auth
def search_and_connect():
    """
    Handles search by service tag, returns device information with authenticated link
    """
    log_request_debug()

    def format_result(
            ndm_hw_id: str,
            token_alias: str,
            system_name: str,
            model_name: str,
            bearer_value: str
    ) -> 'Response':
        """
        Formats result of search_and_connect
        """
        return jsonify(
            {
                'ndmHwId': ndm_hw_id,
                'tokenAlias': token_alias,
                'systemName': system_name,
                'modelName': model_name,
                'bearerValue': bearer_value,
                'redirectUrl': f'https://{system_name}/auth?x-ndma-tkn={bearer_value}&url=/'
            }
        )

    params = extract_parameters_from(request)
    service_tag = params.get('license')
    user_data = params.get('user_data')
    email = params.get('email')

    if not service_tag:
        return format_error('0x200', 'missing license parameter')

    service_tag = ''.join([x for x in service_tag if x.isdigit()])
    if len(service_tag) != 15:  # service tag always contains 15 digits, but sometimes is written with dashes
        return format_error('0x201', 'service tag (license) is not valid')

    try:
        token_alias, system_name, hw_id = ndss_client.resolve_license(service_tag)
    except NDSSException:
        return format_error('0x100', 'failed to get information from NDSS, try later')

    if not token_alias or not system_name:
        return format_error('0x201', 'could not find device by service tag')

    device_data = rs.load_ec_record(token_alias)
    if not device_data:
        # Important: occurs, if device is not linked yet.
        # Later, we need to add method how to call device for registration and linking.
        return format_error('0x300', 'missing keys. is device linked?')

    service_ec_private = device_data.get('serviceEcPrivate')
    service_ec_public = device_data.get('serviceEcPublic')
    if not service_ec_public or not service_ec_private:
        return format_error('0x301', 'failed to load device keys from internal store')

    access_role = 'owner-admin'
    user_data = 'temp;test'

    data = rs.load_bearer_record(token_alias, access_role, user_data)
    if data:
        # If we already have bearer internal record, we need to check if it works
        # by sending remote info request to Keenetic device
        bearer_value = data.get('bearerValue')
        try:
            info_from_device = ndss_client.get_info(token_alias, bearer_value, explained=True)
        except NDSSException:
            return format_error('0x100', 'failed to get information from NDSS, try later')
        except KeeneticDeviceException as kde:
            return format_error(kde.code, kde.description)
        if info_from_device is None:
            # actually, this is not an error, but special case
            return format_error('0x101', 'unexpected answer from NDSS')
        if info_from_device.get('bearer_is_valid') == 'true':
            return format_result(
                hw_id, token_alias, system_name, info_from_device.get('model_name'), bearer_value
            )

    # If we don't have stored bearer record, or bearer value is not valid now,
    # we create new access token, signing and sending it to the device
    try:
        bearer_value, expired_at = ndss_client.trust_token(
            token_alias,
            service_ec_private,
            service_ec_public,
            86400 * 7,
            access_role,
            user_data
        )
    except NDSSException:
        return format_error('0x100', 'failed to get information from NDSS, try later')
    except ECException:
        return format_error('0x302', 'failed to load EC keys')
    except KeeneticDeviceException as kde:
        return format_error(kde.code, kde.description)

    # Preparing and saving bearer record to internal store for future use
    data = rs.prepare_bearer_record(token_alias, access_role, user_data, bearer_value, expired_at)
    rs.save_bearer_record(data)

    try:
        info_from_device = ndss_client.get_info(token_alias, bearer_value, explained=True)
    except NDSSException:
        return format_error('0x100', 'failed to get information from NDSS, try later')
    except KeeneticDeviceException as kde:
        # almost impossible (and not tested)
        return format_error(kde.code, kde.description)

    if info_from_device and info_from_device.get('bearer_is_valid') == 'true':
        return format_result(
            hw_id, token_alias, system_name, info_from_device.get('model_name'), bearer_value
        )
    # just impossible (not tested)
    return format_error('0x404', 'failed to get remote info from Keenetic after sending access token')


@app.route('/', methods=['GET'])
def hello():
    return ''


@app.errorhandler(404)
def not_found():
    log_request_debug()
    return '<h1>Not found</h1>', 404


@app.errorhandler(500)
def server_error():
    log_request_debug()
    return '<h1>An internal error occurred</h1>', 500


if __name__ == '__main__':
    if rs and rs.ensure_infra():
        log(f'Starting web app with service_id={rs.service_id} using {rs.name()} storage')
        app.run()
    else:
        log('Failed to setup environment')
