DEBUG_SKIP_CHECK_TIMESTAMP = False
DEBUG_SKIP_CALLBACK_BASICAUTH = False

RECORDSTORE = 'file'  # 'firestore' or 'file'
RECORDSTORE_DIRPREFIX = '/srv/cloud-link-service-python-example/data'

FIRESTORE_PROJECT = 'your-gcp-project...'

NDSS_SERVICE_ID = '<service-id received from Keenetic>'
NDSS_SERVER = '<NDSS API URL received from Keenetic>'
NDSS_CRT = '4096-KNT-root-ca'
NDSS_TIMEOUT = 30

NDSS_CALLBACK_BASIC_LOGIN = '<Frontend app login>'
NDSS_CALLBACK_BASIC_PASSWORD = '<Frontend app password>'

NDSS_AUTH_BASIC_LOGIN = '<NDSS API login received from Keenetic>'
NDSS_AUTH_BASIC_PASSWORD = '<NDSS API pass received from Keenetic'
