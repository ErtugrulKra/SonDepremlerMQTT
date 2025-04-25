Home Assistant üzerinden MQTT Protokolünü dinleyterek son depremleri ekranınızda dashboardınızda görüntüleyebilirsiniz.

Bunu çalıştırabilmek için Docker Desktop üzerinde 

`docker compose up -d`
komutunu çalıştırdığınızda otomatik olarak ayağa kalkacak ve depremleri dinleyerek MQTT Topic içine kayıt eklemeye başlayacaktır.

Eğer Docker üzerinde bir MQTT Broker kullanmak istemiyorsanız https://mosquitto.org/download/ adresinden Standalone Installer ile yükleyebilirsiniz.

Yine yükledikten sonra uygulamanızda ki verileri debug etmek için aşağıdaki Client çok iş görecektir. 

https://mqtt-explorer.com/
