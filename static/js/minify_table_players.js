var table=new Tabulator("#example-table",{layout:"fitData",columns:[{title:"ID",field:"id",editor:!1},{title:"FIO",field:"fio",editor:"input"},{title:"player_ID",field:"player_id",editor:"number"},],ajaxURL:"/get_data_for_table_players",ajaxConfig:"GET",ajaxResponse:function(e,t,a){return a}});function updateTableFromAjax(){fetch("/get_data_for_table_players").then(e=>{if(e.ok)return e.json();throw Error("Network response was not ok.")}).then(e=>{console.log("Обработка успешного ответа ",e),table.setData(e),table.redraw(!0)}).catch(e=>{console.error("Fetch error:",e)})}document.getElementById("update-button").addEventListener("click",function(){var e=table.getData();$.ajax({url:"http://127.0.0.1:5000/update",type:"POST",contentType:"application/json",data:JSON.stringify(e),success:function(e){alert("Data updated successfully!")}})}),document.addEventListener("DOMContentLoaded",function(){document.getElementById("player-form").addEventListener("submit",function(e){e.preventDefault();let t=document.getElementById("player-fio").value,a=document.getElementById("player-name").value;console.log(t,a),fetch("/update_table_players",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({playerFIO:t,playerName:a})}).then(e=>{if(e.ok)return e.json();throw Error("Network response was not ok.")}).then(e=>{console.log(e),updateTableFromAjax()}).catch(e=>{console.error("Fetch error:",e)})})});