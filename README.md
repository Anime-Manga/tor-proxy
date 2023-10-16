## 🎭Tor Proxy
Questo progetto verrà utilizzato per fare proxy attraverso tor per evitare che venga tracciato e se dovesse bloccare per le troppe richieste viene riavviato con un ip sempre diverso dal precedente.
### Information general:
> Note: `not require` volume mounted on Docker

### Dependencies
| Services | Required |
| ------ | ------ |
| RabbitMQ | ✅  |

### Variabili globali richiesti:
```sh
example:
    #--- General ---
    ADDRESS_RABBIT: "localhost" #"localhost" [default]
    PORT_RABBIT: 9999 #5672 [default]
    USERNAME_RABBIT: "guest" #"guest" [default]
    PASSWORD_RABBIT: "guest" #"guest" [default]
    EXCHANGE_NAME: "example_exchange" [required]
    QUEUE_RABBIT: "example_queue" #"animemanga-tor-proxy" [default]
    REPLICAS: 4 #15 [default]
    EXPECTED_ADDRESS: #ADDRESS_RABBIT [default]
    START_PORT: 9999 #8000 [default]
    PROXY_PATH: "/path/example" #"proxy.txt" [default]
```