# Como Acessar o Sistema na Rede Local

## ⚠️ Importante: Não Precisa de Servidor Dedicado

Qualquer computador na mesma rede pode rodar o sistema. Não é necessário um servidor dedicado - basta que um PC tenha o Django rodando e os outros acessem pelo IP desse PC.

## Como Funciona

1. **PC Principal (Servidor Temporário):** Um computador na rede roda o Django
2. **Outros PCs (Clientes):** Acessam o sistema pelo IP do PC principal
3. **Rede Local:** Todos devem estar na mesma rede Wi-Fi/LAN

## Passos para Iniciar o Servidor na Rede

### 1. Escolher o PC que vai Rodar o Sistema

Qualquer computador na rede pode ser usado. Este PC precisa ter:
- Python instalado
- O projeto Django configurado
- Conexão na mesma rede dos outros PCs

### 2. Iniciar o Servidor Django

No PC escolhido, execute o comando abaixo:

```bash
python manage.py runserver 0.0.0.0:8000
```

**Importante:** Use `0.0.0.0:8000` ao invés de apenas `8000` para permitir conexões externas.

**Ou use o script automático:**
- Execute: `iniciar_servidor_rede.bat`

### 3. Descobrir o IP da Máquina

No PC onde o servidor está rodando, descubra o IP:

```bash
ipconfig | findstr /i "IPv4"
```

Exemplo de saída:
```
Endereço IPv4. . . . . . . .  . . . . . . . : 192.168.18.11
```

### 4. Acessar de Outros Computadores

Nos outros PCs da mesma rede, abra o navegador e acesse:

```
http://192.168.18.11:8000
```

Substitua `192.168.18.11` pelo IP do PC onde o servidor está rodando.

## Exemplo Prático

**Cenário:** Você tem 3 computadores na mesma rede Wi-Fi

1. **No PC 1 (vai rodar o servidor):**
   - Abra o terminal na pasta do projeto
   - Execute: `python manage.py runserver 0.0.0.0:8000`
   - Anote o IP exibido (ex: `192.168.18.11`)

2. **No PC 2 e PC 3 (vão acessar o sistema):**
   - Abra o navegador
   - Digite: `http://192.168.18.11:8000`
   - O sistema estará disponível!

**Nota:** O PC 1 precisa ficar com o terminal aberto enquanto os outros acessam. Se fechar o terminal, o servidor para e os outros não conseguem mais acessar.

## Segurança

⚠️ **ATENÇÃO:** Esta configuração é apenas para desenvolvimento/teste em rede local.

Para produção, você deve:
- Configurar um servidor web (Nginx/Apache)
- Usar HTTPS
- Configurar firewall adequadamente
- Restringir ALLOWED_HOSTS para IPs específicos
- Desabilitar DEBUG = False

## Solução de Problemas

### Não consegue acessar de outros dispositivos?

1. **Verifique o firewall do Windows:**
   - Permita conexões na porta 8000
   - Ou desative temporariamente o firewall para teste

2. **Verifique se está na mesma rede:**
   - Todos os dispositivos devem estar na mesma rede Wi-Fi/LAN

3. **Verifique o IP:**
   - O IP pode mudar se a conexão for reiniciada
   - Execute `ipconfig` novamente para verificar

4. **Teste localmente primeiro:**
   - Acesse `http://localhost:8000` na própria máquina
   - Se funcionar, o problema é de rede/firewall

## Comando Rápido

Para iniciar rapidamente na rede:
```bash
python manage.py runserver 0.0.0.0:8000
```

Depois acesse de qualquer dispositivo na rede usando:
```
http://192.168.18.11:8000
```
