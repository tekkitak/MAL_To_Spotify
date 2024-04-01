$().ready(function() {
    const ctx = document.getElementById('myChart');
    // get data from ajax request

    $.ajax({
        url: '/api/statistics/bySong',
        type: 'GET',
        data: {
            limit: 10,
            offset: 0
        },
        success: function(data) {
            labels = []
            final_data = []
            data = JSON.parse(data)
            data['data'].forEach(function(item) {
                labels.push(item['song_title'])
                final_data.push(item['count'])
            });
            console.log(labels)
            console.log(final_data)

            new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                label: 'Number of times imported',
                data: final_data,
                borderWidth: 1
                }]
            },
            options: {
                scales: {
                y: {
                    beginAtZero: true
                }
                }
            }
            });
        }
    });

});