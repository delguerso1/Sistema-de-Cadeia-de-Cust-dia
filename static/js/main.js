// Validação de formulário e funcionalidades JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Botão de selecionar pasta (funcionalidade básica)
    const btnSelecionarPasta = document.getElementById('btn-selecionar-pasta');
    const inputCaminhoPasta = document.getElementById('caminho-pasta');
    
    if (btnSelecionarPasta && inputCaminhoPasta) {
        btnSelecionarPasta.addEventListener('click', function() {
            // Nota: Por limitações de segurança do navegador, não é possível
            // abrir um seletor de pasta diretamente. O usuário precisa digitar o caminho.
            // Em uma aplicação desktop (Electron) ou com permissões especiais, isso seria possível.
            alert('Por favor, digite o caminho completo da pasta no campo acima.\n\nExemplo: C:\\Videos\\Caso_001');
            inputCaminhoPasta.focus();
        });
    }
    
    // Validação de formulário
    const form = document.getElementById('custodia-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            // Validação específica do caminho da pasta
            const caminhoPasta = inputCaminhoPasta ? inputCaminhoPasta.value.trim() : '';
            if (caminhoPasta && !caminhoPasta.match(/^[A-Za-z]:\\.*/)) {
                alert('Por favor, insira um caminho válido no formato Windows (ex: C:\\Pasta\\Videos)');
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
                alert('Por favor, preencha todos os campos obrigatórios.');
            }
        });
    }
    
    // Formatação automática de data/hora
    const dataColetaInput = document.querySelector('input[type="datetime-local"]');
    if (dataColetaInput && !dataColetaInput.value) {
        // Definir data/hora atual como padrão
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        dataColetaInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    
    // Feedback visual nos campos
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value.trim()) {
                this.classList.add('filled');
            } else {
                this.classList.remove('filled');
            }
        });
        
        input.addEventListener('input', function() {
            this.classList.remove('error');
        });
    });
});

// Função para copiar hash (usada na página de resultado)
function copiarHash() {
    const hashElement = document.querySelector('.hash-code');
    if (hashElement) {
        const hash = hashElement.textContent.trim();
        
        // Criar elemento temporário para copiar
        const tempInput = document.createElement('input');
        tempInput.value = hash;
        document.body.appendChild(tempInput);
        tempInput.select();
        tempInput.setSelectionRange(0, 99999); // Para mobile
        
        try {
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            
            // Feedback visual
            const btnCopy = document.querySelector('.btn-copy');
            if (btnCopy) {
                const originalText = btnCopy.textContent;
                btnCopy.textContent = '✓ Copiado!';
                btnCopy.style.background = '#28a745';
                
                setTimeout(function() {
                    btnCopy.textContent = originalText;
                    btnCopy.style.background = '#28a745';
                }, 2000);
            }
        } catch (err) {
            console.error('Erro ao copiar:', err);
            alert('Erro ao copiar. Por favor, selecione e copie manualmente.');
        }
    }
}

// Função para formatar caminho de pasta (Windows)
function formatarCaminhoPasta(caminho) {
    // Remove espaços extras e normaliza barras
    return caminho.trim().replace(/\//g, '\\');
}
