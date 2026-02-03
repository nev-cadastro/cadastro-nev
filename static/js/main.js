// ============================================================================
// Sistema NEV USP - JavaScript Principal
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // Formatação automática de CPF
    const cpfInputs = document.querySelectorAll('input[name="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.substring(0, 11);
            
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            }
            e.target.value = value;
        });
    });

    // Formatação automática de telefone
    const telInputs = document.querySelectorAll('input[name="celular"], input[name="telefone_pessoal"], input[name="telefone_comercial"]');
    telInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length === 11) {
                value = value.replace(/(\d{2})(\d)/, '($1) $2');
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
            } else if (value.length === 10) {
                value = value.replace(/(\d{2})(\d)/, '($1) $2');
                value = value.replace(/(\d{4})(\d)/, '$1-$2');
            }
            e.target.value = value;
        });
    });

    // Formatação automática de CEP
    const cepInputs = document.querySelectorAll('input[name="cep"]');
    cepInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) value = value.substring(0, 8);
            
            if (value.length === 8) {
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
            }
            e.target.value = value;
        });
    });

    // Confirmação para exclusões
    const deleteButtons = document.querySelectorAll('.btn-delete, form[action*="excluir"] button[type="submit"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide flash messages após 5 segundos
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
        flashMessages.forEach(message => {
            const fadeEffect = setInterval(() => {
                if (!message.style.opacity) {
                    message.style.opacity = 1;
                }
                if (message.style.opacity > 0) {
                    message.style.opacity -= 0.1;
                } else {
                    clearInterval(fadeEffect);
                    message.style.display = 'none';
                }
            }, 50);
        });
    }, 5000);

    // Tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Busca de CEP via API (se o campo CEP existir)
    const cepField = document.querySelector('input[name="cep"]');
    if (cepField) {
        cepField.addEventListener('blur', function(e) {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                buscarCEP(cep);
            }
        });
    }

    // Validação de formulários
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Alternar visibilidade de senha
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    });

});

// Função para buscar CEP
function buscarCEP(cep) {
    fetch(`https://viacep.com.br/ws/${cep}/json/`)
        .then(response => response.json())
        .then(data => {
            if (!data.erro) {
                document.querySelector('input[name="endereco"]').value = data.logradouro || '';
                document.querySelector('input[name="bairro"]').value = data.bairro || '';
                document.querySelector('input[name="cidade"]').value = data.localidade || '';
                document.querySelector('select[name="estado"]').value = data.uf || '';
            } else {
                alert('CEP não encontrado!');
            }
        })
        .catch(error => {
            console.error('Erro ao buscar CEP:', error);
        });
}

// Função para exportar dados
function exportarDados(formato) {
    const url = `/exportar/colaboradores/${formato}`;
    window.location.href = url;
}

// Função para pesquisar colaboradores (auto-complete)
function pesquisarColaboradores(query) {
    if (query.length < 2) return;
    
    fetch(`/api/colaboradores?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            // Implementar lógica de auto-complete aqui
            console.log('Resultados:', data.results);
        });
}