/*global Tabulator */
// Создание таблицы
let table = new Tabulator("#example-table", {
    height: 400,
    // width: "100%",
    layout: "fitData",
    columns: [
        // {title: "ID", field: "id", editor: false},
        {title: "ФИО", field: "fio", editor: "input"},
        {title: "ID игрока", field: "player_id", editor: "number"},
        {title: "Команда", field: "team_name", editor: "number"},
    ],
    // autoColumns: true,
    ajaxURL: "/get_data",
    ajaxConfig: "GET",
});

// Функция для обновления данных в таблице через AJAX и перерисовки
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
    document.getElementById('player-form').addEventListener('submit', function (event) {
        event.preventDefault(); // Предотвращаем отправку формы по умолчанию

        let playerFIO = document.getElementById('player-fio').value;
        let playerName = document.getElementById('player-name').value;
        let teamName = document.getElementById('player-team').value;
        console.log(playerFIO, playerName, teamName);
        let postData = {
            playerFIO: playerFIO,
            playerName: playerName,
            teamName: teamName
        };

        // Отправка данных на сервер с использованием метода POST
        fetch('/update_table_players', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
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