#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stddef.h>
#include <unistd.h>

#define ADRES_SERWERA "127.0.0.1"
#define PORT_SERWERA 15123
#define DLUGOSC_KOLEJKI_OCZEKUJACYCH_POLACZEN 10

int main() {
  struct sockaddr_in endpoint = {
    .sin_family = AF_INET,
    .sin_port = htons(PORT_SERWERA),
    .sin_addr.s_addr = inet_addr(ADRES_SERWERA)
  };

  int socket_descriptor = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

  bind(socket_descriptor, (struct sockaddr*)&endpoint, sizeof(endpoint));

  listen(socket_descriptor, DLUGOSC_KOLEJKI_OCZEKUJACYCH_POLACZEN);

  for (;;) {
    int connection_descriptor = accept(socket_descriptor, NULL, NULL);

    /*
      Interakcje z klientem
    */
    
    shutdown(connection_descriptor, SHUT_RDWR);
    close(connection_descriptor);
  }

  return 0;
}

