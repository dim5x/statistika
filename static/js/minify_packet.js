$(document).ready(function(){let e=1;$("#add-input").click(function(){e++,$("#input-container").append('<div class="input-group"><label for="game-name-'+e+'">ID пакета: </label><input type="text" id="game-name-'+e+'" name="game-name[]"></div>')}),$("#game-form").submit(function(e){e.preventDefault();let n=[];$('input[name="game-name[]"]').each(function(){n.push($(this).val())}),console.log(n),fetch("/packet",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)}).then(e=>{if(e.ok)return e.json();throw Error("Network response was not ok.")}).then(e=>{console.log(e),(d=document.getElementById("serverResponse")).innerHTML="",d.innerHTML=e.data.split("\n")}).catch(e=>{console.error("Fetch error:",e)})})});