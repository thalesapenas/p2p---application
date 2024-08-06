# Aplicação P2P para Troca de Arquivos em Rede Local

Esta aplicação permite a troca de arquivos entre hosts na mesma rede local utilizando uma arquitetura peer-to-peer (P2P). Siga os passos abaixo para configurar e utilizar a aplicação.

## Como Usar

1. **Inicie o Servidor:**
   - Execute o servidor passando a porta que deseja que ele escute. Por exemplo:
     ```bash
     servidor --porta 12345
     ```

2. **Inicie os Peers:**
   - Execute quantos peers desejar, passando a porta que cada um deve operar. Por exemplo:
     ```bash
     peer --porta 23456
     ```

3. **Conecte os Peers ao Servidor:**
   - Conecte todos os peers ao servidor utilizando as opções de configuração disponíveis. Após a conexão, envie a lista de peers para todos os peers conectados.

4. **Utilize as Opções do Peer:**
   - Agora que todos os peers estão conectados e a lista de peers foi distribuída, você pode usar as opções disponíveis no peer para trocar arquivos.

Certifique-se de que todos os peers e o servidor estejam na mesma rede local para garantir o funcionamento correto da aplicação.
