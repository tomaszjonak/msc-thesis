Repozytorium zawiera zarowno kod klienta, serwera oraz aplikacji symulujacej stanowisko pomiarowe

## Zgrubny schemat dzialania

Aplikacje komunikuja sie miedzy soba za pomoca protokolu tcp, maja zaszyte "na sztywno" podstawowe wartosci realizujace komunikacje
po interfejsie lokalnym. Uproszczony schemat:

data provider <- 50321 -> client <- 50123 -> server

Gdzie liczby na polaczeniach to numery portow

Provider oraz server sa aplikacjami pasywnymi, czekaja na polaczenie ktore inicjuje klient

### Lokalizacje na dysku

Do poprawnego dzialania klient oraz data provider potrzebuja miec ustawiony tzw storage_root na ten sam katalog, inaczej klient nie znajdzie plikow do wyslania

Storage root serwera musi byc ustawiony na inny katalog (inaczej nadpisze pliki) i odwzoruje on strukture katalogow ktora znajduje sie na kliencie.

## Konfiguracja data providera (aplikacja wysylajaca juz istniejace pliki)

Katalog roboczy: implementacja2
$ python sync/labview_sim/data_provider.py -hs <host> -p <port> -s <sciezka do katalogu z pomiarami> -e <rozszerzenia plikow rozdzielone spacjami>

Aplikacja przeszukuje podany katalog rekurencyjnie, znajdujac wszystkie pliki o podanych rozszerzeniach, sortuje je (z tego powodu musza miec schemat nazewnicta generowany z labview)
a nastepnie wysyla zgodnie z zadanym trybem. Sciezki plikow interpretowane sa relatywnie do katalogu podanego w parametrze '-s'.

Aplikacja posiada dwa tryby:
    interkatywny (domyslny)
    automatyczny

W pierwszym z nich aby wyslac informacje o pojawieniu sie nowego pliku do klienta nalezy wcisnac enter, mozna rowniez pominac plik - w tym celu trzeba wpisac dowolny znak przed enterem. Tryb interaktywny zacznie pracowac w momencie gdy zostanie nawiazane polaczeni z klientem.
Tryb automatyczny wymaga uzycia dodatkowej flagi '-sl <interwal w sekundach>', aplikacja rozglasza wtedy nowy plik co zadany interwal. Mozna rowniez podac dodatkowy parametr -sk (skip) ktory sprawia ze aplikacja ignoruje n pierwszych wpisow, uzyteczne do zaobserwowania dzialania synchronizacji.

Istnieje rowniez aplikacja generujaca losowe dane jednak przy uzyciu kompresji nie wydaje sie zbyt uzyteczna.

## Konfiguracja servera

Katalog roboczy: katalog implementacja2
$ ./server.py
Bez parametrow server bedzie nasluchiwal na adresie 127.0.0.1:50123, uruchomienie go utworzy rowniez plik state_storage/server.cache (pozostalosc po poprzednim podejsciu do synchronizacji)
Opcje mozna modyfikowac albo podajac plik konfiguracyjny albo ustawiajac wartosci z konsoli

Struktura pliku konfiguracyjnego (format json, sa to rowniez wartosci domyslne zaszyte w kodzie)
{
  "host": "127.0.0.1",
  "port": 50123,
  "cache_path": "state_storage/server.cache",
  "storage_root": "server_storage"
}

Zakladajac ze plik konfiguracyjny znajduje sie w tym samym katalogu i nazywa sie server.json odpalamy server komenda
./server.py -c server.json

Nadpisac opcje mozna za pomoca nazw
./server.py -o host 192.168.1.100

Opcje nadpisane z konsoli maja wyzszy priorytet niz podane w konfiguracji, jesli podamy kilkukrotnie ten sam klucz opcji (np host) ostatnia wartosc zostanie uzyta

## Konfiguracja klienta

Katalog roboczy: implementacja2
Sposob konfiguracji analogicznie do serwera, domyslnie sprobouje sie polaczyc na adresy 127.0.0.1:50123 oraz 127.0.0.1:50321, jesli to sie nie uda bedzie ponawial polaczeni co zadany interwal (paramter retry_time w konfiguracji)

Struktura pliku konfiguracyjnego (wartosci domyslne):
{
  "server": {                                                                                                                                                                                                      
    "host": "127.0.0.1",                                                                                                                                                                                           
    "port": 50123,                                                                                       
    "retry_time": 30,                                                                                    
    "processor": "compression"                                                                           
  },                                                                                                     
  "provider": {                                                                                          
    "host": "127.0.0.1",                                                                                                                                                                                           
    "port": 50321,                                                                                       
    "extensions": [                                                                                                                                                                                                
      "lvm",                                                                                                                                                                                                       
      "avi"                                                                                                                                                                                                        
    ],                                                                                                                                                                                                             
    "retry_time": 30,                                                                                    
    "separator": "\n"                                                                                                                                                                                              
  },                                                                                                     
  "storage_root": "client_storage",
  "stage_queue_path": "state_storage/stage.queue",
  "cache_path": "state_storage/client.cache"
}

Zmiana wartosci za pomoca opcji w przypadku zagniezdzonym:
$ ./client.py -o server.host 192.168.0.1 -o storage_root /sciezka/do/katalogu/pomiarow

### Usuwanie plikow po otrzymaniu odpowiedzi z serwera

Aby uzyc tego trybu nalezy dodac flage --delete_acknowledged przy odpalaniu klienta

TODO: szerszy opis konfiguracji klienta

## Rozruch testowy na localhoscie (jak bylo testowane)

Idealnie jest sobie ustawic trzy okna konsoli (jakims programem do terminali, np tmuxem) i odpalic clienta na koncu, inaczej trzeba czekac do ponownej proby nawiazania polaczenia
Pliki ze stanem klienta oraz serwera znajdowaly sie w katalogu state_storage, dane klienta wziete z traffic2 w client_storage a storage_root serwera w katalogu server_storage

Sekwencja odpalania, katalog roboczy implementacja2
Konsola 1: $ python sync/labview_sim/data_provider.py -hs 127.0.0.1 -p 50321 -s client_storage -e lvm avi
Konsola 2: $ ./server.py
Konsola 3: $ ./client.py

Aby rozglaszac kolejne pliki wystarczy klikac enter w Konsoli 1

Test z uzyciem innej maszyny (vmka/docker/inny host) w najprostszym wypadku wymaga zmiany adresow ip oraz ustawienia storage_root klienta i symulatora na poprawna sciezke
Zalozmy ze host z klientem ma adres 192.168.0.100 i zawiera pomiary w katalogu /mnt/d/pomiary a host z serwerem 192.168.0.200 i chcemy aby pomiary na serwerze pojawily sie w katalogu pomiary_gardawice znajdujacym sie w katalogu domowym uzytkownika. Katalog roboczy jak poprzednio

Host 1:
python python sync/labview_sim/data_provider.py -hs 127.0.0.1 -p 50321 -s /mnt/d/pomiary -e lvm avi
./client.py -o server.host 192.168.0.200 -o storage_root /mnt/d/pomiary
Host 2:
./server.py -o host 192.168.0.200 -o storage_root ~/pomiary_gardawice

## Konfiguracja schematow kompresji

Dodam w najblizszym czasie, jeszcze nie jest gotowa


## Poziom szczegolowosci logow

Nalezy zmienic wartosc root.level w pliku logging.json, najwieksza szczegolowosc daje wartosc DEBUG

Szersza dokumentacja: https://docs.python.org/3/library/logging.config.html