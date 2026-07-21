const zone = document.getElementById("drop-zone");
const input = document.getElementById("file-input");
const status = document.getElementById("status");

function getUserNo() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlUserNo = urlParams.get("user_no");

    if (urlUserNo) {
        localStorage.setItem("user_no", urlUserNo);
        return urlUserNo;
    }

    const userNo = localStorage.getItem("user_no");
    if (!userNo) {
        status.innerHTML = "❌ Session expired. Please log in again.";
        return null;
    }
    return userNo;
}

zone.onclick = () => input.click();

input.onchange = () => {
    const userNo = getUserNo();
    if (userNo && input.files[0]) {
        upload(input.files[0], userNo);
    }
};

zone.addEventListener("dragover", (e) => {
    e.preventDefault();
});

zone.addEventListener("drop", (e) => {
    e.preventDefault();
    const userNo = getUserNo();
    if (userNo && e.dataTransfer.files[0]) {
        upload(e.dataTransfer.files[0], userNo);
    }

});

async function upload(file, userNo) {
    if (!file || !userNo) return;
    
    status.innerHTML = "Uploading & processing...";

    const form = new FormData();
    form.append("file", file);
    form.append("user_no", userNo);

    try{
        const API_URL = "http://127.0.0.1:8000";

        const response=await fetch(`${API_URL}/extract`, {
            method:"POST",
            body:form

        });
        const result=await response.json();

        if (response.ok && result.status === "success") {
            status.innerHTML="✅ Upload Complete";
            console.log(result);
        } else {
            status.innerHTML = "❌ Processing Failed";
            console.error(result.message);
        }
    } catch(err){
        status.innerHTML="❌ Upload Failed";
        console.error(err);
    }
}