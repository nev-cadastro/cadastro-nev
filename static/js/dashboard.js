// Gráficos do Dashboard (usando Chart.js se disponível)
document.addEventListener('DOMContentLoaded', function() {
    
    // Gráfico de distribuição por vínculo (exemplo)
    const vinculosChart = document.getElementById('vinculosChart');
    if (vinculosChart) {
        // Este código assume que você tem dados no HTML via data attributes
        const ctx = vinculosChart.getContext('2d');
        const labels = JSON.parse(vinculosChart.dataset.labels || '[]');
        const data = JSON.parse(vinculosChart.dataset.values || '[]');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#003366', // Azul USP
                        '#C41230', // Vermelho USP
                        '#28a745', // Verde
                        '#17a2b8', // Azul claro
                        '#ffc107', // Amarelo
                        '#dc3545', // Vermelho
                        '#6c757d', // Cinza
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
    
    // Gráfico de novos cadastros (exemplo)
    const novosCadastrosChart = document.getElementById('novosCadastrosChart');
    if (novosCadastrosChart) {
        // Implementar gráfico de linha para novos cadastros
    }
    
});