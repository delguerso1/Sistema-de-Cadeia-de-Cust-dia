# Solução para Acesso na Rede Local

## Problema Identificado

O servidor estava rodando apenas em `127.0.0.1:8000` (localhost), o que impede acesso de outros computadores.

## Solução

### Opção 1: Usar o Script Automático (Recomendado)

1. **Execute o arquivo:** `iniciar_servidor_rede.bat`
   - Este script detecta automaticamente seu IP
   - Inicia o servidor na rede corretamente

### Opção 2: Comando Manual

Execute no terminal:
```bash
python manage.py runserver 0.0.0.0:8000
```

**IMPORTANTE:** Use `0.0.0.0:8000` e não apenas `8000` ou `127.0.0.1:8000`

## Verificar se Está Funcionando

Após iniciar o servidor, verifique se está escutando corretamente:

```bash
netstat -ano | findstr :8000
```

Você deve ver algo como:
```
TCP    0.0.0.0:8000         0.0.0.0:0              LISTENING
```

Se aparecer apenas `127.0.0.1:8000`, o servidor não está acessível na rede.

## Configurar Firewall do Windows

Se ainda não conseguir acessar, configure o firewall:

### Método 1: Interface Gráfica
1. Abra "Firewall do Windows Defender"
2. Clique em "Configurações Avançadas"
3. Clique em "Regras de Entrada" → "Nova Regra"
4. Escolha "Porta" → Próximo
5. Selecione "TCP" e digite `8000` → Próximo
6. Escolha "Permitir a conexão" → Próximo
7. Marque todos os perfis → Próximo
8. Nome: "Django Server 8000" → Concluir

### Método 2: PowerShell (Como Administrador)
```powershell
New-NetFirewallRule -DisplayName "Django Server 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

## Testar Acesso

**Importante:** Qualquer PC na rede pode ser o servidor. Não precisa de servidor dedicado.

1. **No PC que vai rodar o sistema:**
   - Execute: `python manage.py runserver 0.0.0.0:8000`
   - Anote o IP exibido (ex: `192.168.18.11`)
   - **Mantenha o terminal aberto** enquanto outros acessam

2. **Nos outros computadores da mesma rede:**
   - Abra o navegador
   - Digite: `http://192.168.18.11:8000` (use o IP do PC servidor)
   - Deve carregar a página

## Verificar IP Atual

Se o IP mudou, descubra o novo:
```bash
ipconfig | findstr /i "IPv4"
```

## Checklist de Diagnóstico

- [ ] Um PC escolhido para rodar o servidor (qualquer PC na rede serve)
- [ ] Servidor iniciado com `0.0.0.0:8000` (não `127.0.0.1`)
- [ ] Firewall permite porta 8000 no PC servidor
- [ ] Todos os PCs na mesma rede Wi-Fi/LAN
- [ ] IP correto do PC servidor (verificar com `ipconfig`)
- [ ] Testar primeiro em `http://localhost:8000` no próprio PC servidor
- [ ] Terminal do servidor permanece aberto enquanto outros acessam

## Comandos Úteis

**Ver processos na porta 8000:**
```bash
netstat -ano | findstr :8000
```

**Parar servidor:**
- Pressione `Ctrl+C` no terminal onde está rodando

**Verificar conexões ativas:**
```bash
netstat -an | findstr ESTABLISHED | findstr :8000
```
