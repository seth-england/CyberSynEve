
// States
export const CSE_STATE_INIT = 0
export const CSE_STATE_WELCOME = 1
export const CSE_STATE_MAIN = 2

// URLs
//export const CSE_SERVER_URL = 'http://192.168.50.219:5000' // Main
export const CSE_SERVER_URL = 'http://127.0.0.1:5000'
export const CSE_PING_URL = CSE_SERVER_URL + '/ping'
export const SERVER_AUTH_ENDPOINT = '/auth'
export const SERVER_AUTH_URL = CSE_SERVER_URL + SERVER_AUTH_ENDPOINT
export const SERVER_CLIENT_SETTINGS_ENDPOINT = '/clientsettings'
export const SERVER_CLIENT_SETTINGS_URL = CSE_SERVER_URL + SERVER_CLIENT_SETTINGS_ENDPOINT
export const SERVER_CHARACTERS_ENDPOINT = '/characters'
export const SERVER_CHARACTERS_URL = CSE_SERVER_URL + SERVER_CHARACTERS_ENDPOINT


// Other
export const SCOPES = 'publicData esi-location.read_location.v1 esi-location.read_ship_type.v1 esi-wallet.read_character_wallet.v1 esi-markets.read_character_orders.v1'
export const CLIENT_ID = 'ba636c6aeae54c8386770bc919ef2bca'
