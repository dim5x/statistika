// Создание таблицы
var table = new Tabulator("#table_teams", {
    // height: 205,
    // width: "100%",
    layout: "fitDataFill",
    columns: [
        // {title: "ID", field: "id", editor: false},
        {title: "Name", field: "Name", editor: "input"},
        // {title: "player_ID", field: "player_id", editor: "number"},
    ],
    // autoColumns: true,
    ajaxURL: "/get_data",
    ajaxConfig: "GET",
    ajaxResponse: function (url, params, response) {
        return response;
    },
});

function updateTableFromAjax() {
    fetch('/get_data')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response was not ok.');
        })
        .then(data => {
            console.log('Обработка успешного ответа ', data); // Обработка успешного ответа от сервера
            table.setData(data); // Установка новых данных из AJAX-ответа
            table.redraw(true); // Обновление таблицы

        })
        .catch(error => {
            console.error('Fetch error:', error); // Обработка ошибок
        });
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('team-form').addEventListener('submit', function (event) {
        event.preventDefault(); // Предотвращаем отправку формы по умолчанию

        let team_name = document.getElementById('team-name').value;
        console.log(team_name);
        let postData = {
            team_name: team_name
        };

        // Отправка данных на сервер с использованием метода POST
        fetch('/update_table_teams', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(postData)
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok.');
            })
            .then(data => {
                console.log(data); // Обработка успешного ответа от сервера
                updateTableFromAjax();
            })
            .catch(error => {
                console.error('Fetch error:', error); // Обработка ошибок
            });
    });
});