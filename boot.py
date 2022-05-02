import network

wlan = network.WLAN(network.STA_IF)
if not wlan.isconnected():
    print('connecting to network...')
    wlan.active(True)
    wlan.connect('VM-5GHz', 'overthehill')
    while not wlan.isconnected():
        pass
print('network config:', wlan.ifconfig())