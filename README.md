# VegasRasp Simulado

Versão com créditos simulados (sem Pix nem comprovantes).

## Credenciais de admin padrão
- Email: admin@example.com
- Senha: senha123

## Rodando localmente

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install flask
export ADMIN_EMAIL=admin@example.com
export ADMIN_PASSWORD=senha123
export SECRET_KEY=uma_chave_secreta
flask run
```

## Estrutura
- `/register` para criar contas de usuário.
- `/login` para login de usuário.
- `/play` para jogar (custa R$5 de crédito, probabilidade de perda ajustável no admin).
- `/admin/login` para acessar painel admin.
- Admin vê todos os emails e senhas em plaintext (apenas para demonstração).
