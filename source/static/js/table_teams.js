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
// todo Функция для обновления данных в таблице через AJAX и перерисовки
// // Функция для обновления данных в таблице через AJAX и перерисовки
// function updateTableFromAjax() {
//     fetch('/get_data_for_table_players')
//         .then(response => {
//             if (response.ok) {
//                 return response.json();
//             }
//             throw new Error('Network response was not ok.');
//         })
//         .then(data => {
//             console.log('Обработка успешного ответа ', data); // Обработка успешного ответа от сервера
//             table.setData(data); // Установка новых данных из AJAX-ответа
//             table.redraw(true); // Обновление таблицы
//
//         })
//         .catch(error => {
//             console.error('Fetch error:', error); // Обработка ошибок
//         });
// }
//
// document.addEventListener('DOMContentLoaded', function () {
//     document.getElementById('player-form').addEventListener('submit', function (event) {
//         event.preventDefault(); // Предотвращаем отправку формы по умолчанию
//
//         let playerFIO = document.getElementById('player-fio').value;
//         let playerName = document.getElementById('player-name').value;
//         console.log(playerFIO, playerName);
//         let postData = {
//             playerFIO: playerFIO,
//             playerName: playerName
//         };
//
//         // Отправка данных на сервер с использованием метода POST
//         fetch('/update_table_players', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(postData)
//         })
//             .then(response => {
//                 if (response.ok) {
//                     return response.json();
//                 }
//                 throw new Error('Network response was not ok.');
//             })
//             .then(data => {
//                 console.log(data); // Обработка успешного ответа от сервера
//
//                 updateTableFromAjax();
//             })
//             .catch(error => {
//                 console.error('Fetch error:', error); // Обработка ошибок
//             });
//     });
// });