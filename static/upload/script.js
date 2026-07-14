const zone = document.getElementById("drop-zone");
const input = document.getElementById("file-input");
const status = document.getElementById("status");

zone.onclick = () => input.click();

input.onchange = () => {
    upload(input.files[0]);
};

zone.addEventListener("dragover", (e) => {
    e.preventDefault();
});

zone.addEventListener("drop", (e) => {
    e.preventDefault();
    upload(e.dataTransfer.files[0]);

});

async function upload(file){
    if(!file) return;
    status.innerHTML="Uploading...";
    const form=new FormData();
    form.append("file",file);

    try{
        const API_URL = "http://127.0.0.1:8000";

        const response=await fetch("/extract",{
            method:"POST",
            body:form

        });
        const result=await response.json();
        status.innerHTML="✅ Upload Complete";
        console.log(result);
        setTimeout(()=>{
            window.close();
        },1500);

    }

    catch(err){
        status.innerHTML="❌ Upload Failed";
    }

}