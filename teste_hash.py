from werkzeug.security import generate_password_hash, check_password_hash

print("Teste de hash do werkzeug")
print("=" * 40)

# Teste 1: Gerar e verificar
senha = "AdminNEV2024"
hash_result = generate_password_hash(senha)
print(f"Senha: {senha}")
print(f"Hash: {hash_result[:60]}...")
print(f"check_password_hash funciona? {check_password_hash(hash_result, senha)}")
print(f"check_password_hash com senha errada? {check_password_hash(hash_result, 'errada')}")

# Teste 2: Com método específico
hash_pbkdf2 = generate_password_hash(senha, method='pbkdf2:sha256', salt_length=16)
print(f"\nHash PBKDF2 específico: {hash_pbkdf2[:60]}...")
print(f"Verificação: {check_password_hash(hash_pbkdf2, senha)}")

# Teste 3: O hash que está no banco
hash_atual = "pbkdf2:sha256:600000$ybQ0GHw0u..."  # apenas exemplo
print(f"\nHash atual começa com: {hash_atual[:30]}")