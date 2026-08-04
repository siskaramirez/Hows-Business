const API_URL = "http://127.0.0.1:8000";
const accountTypes = ["Asset", "Liability", "Equity", "Revenue", "Expense"];
const paymentMethods = ["Cash", "Gcash", "Maya"];
const transactionTypes = [
    "Cash",
    "Kitchen Equipment",
    "Inventory",
    "Accounts Payable",
    "Loans Payable",
    "Lease Liability",
    "Owner's Equity",
    "Retained Earnings",
    "Food Sales",
    "Beverage and Snack Sales",
    "Cost of Goods Sold (COGS)",
    "Canteen Rent Expense",
    "Utilities Expense",
    "Sales",
    "Rent Expense",
    "Office Supplies",
    "Service Revenue",
    "Cost of Goods Sold",
    "Equipment",
];

const uploadPanel = document.getElementById("upload-panel");
const reviewPanel = document.getElementById("review-panel");
const zone = document.getElementById("drop-zone");
const input = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const reviewStatus = document.getElementById("review-status");
const reviewSummary = document.getElementById("review-summary");
const reviewBody = document.getElementById("review-body");
const confirmButton = document.getElementById("confirm-import");
const pinModal = document.getElementById("pin-modal");
const pinDigits = [...document.querySelectorAll(".pin-digit")];
const pinStatus = document.getElementById("pin-status");
const verifyPinButton = document.getElementById("verify-pin");

let previewFileName = "";

function getUserNo() {
    const params = new URLSearchParams(window.location.search);
    const userNo = params.get("user_no");
    return userNo ? Number(userNo) : null;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function options(values, selected) {
    const placeholder = values.includes(selected)
        ? ""
        : '<option value="" selected>Choose...</option>';
    return placeholder + values.map((value) => (
        `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>` +
        `${escapeHtml(value)}</option>`
    )).join("");
}

function showUploader() {
    reviewPanel.hidden = true;
    uploadPanel.hidden = false;
    reviewStatus.textContent = "";
    reviewBody.innerHTML = "";
    input.value = "";
}

function renderPreview(records) {
    reviewBody.innerHTML = records.map((record, index) => `
        <tr class="review-row">
            <td class="row-number">${index + 1}</td>
            <td><input data-field="transaction_date" type="date" value="${escapeHtml(record.transaction_date)}"></td>
            <td><input data-field="description" type="text" value="${escapeHtml(record.description)}"></td>
            <td><select data-field="account_name">${options(accountTypes, record.account_name)}</select></td>
            <td><input data-field="amount" type="number" min="0.01" step="0.01" value="${escapeHtml(record.amount)}"></td>
            <td><select data-field="payment_method">${options(paymentMethods, record.payment_method)}</select></td>
            <td><select data-field="transaction_type">${options(transactionTypes, record.transaction_type)}</select></td>
            <td><input data-field="invoice_no" type="text" maxlength="20" value="${escapeHtml(record.invoice_no)}"></td>
            <td><button class="remove-row" type="button" title="Remove row">&times;</button></td>
        </tr>
    `).join("");

    renumberRows();
    uploadPanel.hidden = true;
    reviewPanel.hidden = false;
    reviewSummary.textContent = `${records.length} extracted row${records.length === 1 ? "" : "s"} from ${previewFileName}`;
}

function renumberRows() {
    [...reviewBody.querySelectorAll(".review-row")].forEach((row, index) => {
        row.querySelector(".row-number").textContent = index + 1;
    });
}

function collectAndValidate() {
    const rows = [...reviewBody.querySelectorAll(".review-row")];
    const records = [];
    const invoices = new Set();
    let valid = rows.length > 0;

    rows.forEach((row) => {
        const record = {};
        row.querySelectorAll("[data-field]").forEach((field) => {
            field.classList.remove("invalid");
            record[field.dataset.field] = field.value.trim();
        });
        record.amount = Number(record.amount);

        row.querySelectorAll("[data-field]").forEach((field) => {
            const value = record[field.dataset.field];
            const invalid = value === "" || value === null ||
                (field.dataset.field === "amount" && (!Number.isFinite(value) || value <= 0));
            if (invalid) {
                field.classList.add("invalid");
                valid = false;
            }
        });

        const invoiceField = row.querySelector('[data-field="invoice_no"]');
        if (invoices.has(record.invoice_no)) {
            invoiceField.classList.add("invalid");
            valid = false;
        }
        invoices.add(record.invoice_no);
        records.push(record);
    });

    if (!valid) {
        reviewStatus.textContent = "Correct the highlighted fields before importing.";
        reviewStatus.className = "status error";
        return null;
    }
    return records;
}

async function extractFile(file) {
    const userNo = getUserNo();
    if (!userNo) {
        uploadStatus.textContent = "Session expired. Please log in again.";
        uploadStatus.className = "status error";
        return;
    }
    if (!file || !file.name.toLowerCase().endsWith(".xlsx")) {
        uploadStatus.textContent = "Select a valid .xlsx file.";
        uploadStatus.className = "status error";
        return;
    }

    uploadStatus.textContent = "Extracting rows with R...";
    uploadStatus.className = "status";
    const form = new FormData();
    form.append("file", file);
    form.append("user_no", userNo);

    try {
        const response = await fetch(`${API_URL}/extract`, { method: "POST", body: form });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || "Extraction failed.");
        }
        previewFileName = result.file_name;
        renderPreview(result.records || []);
    } catch (error) {
        uploadStatus.textContent = error.message;
        uploadStatus.className = "status error";
    }
}

async function confirmImport() {
    const records = collectAndValidate();
    if (!records) return;

    confirmButton.disabled = true;
    reviewStatus.textContent = "Validating and creating dual-entry records...";
    reviewStatus.className = "status";
    try {
        const response = await fetch(`${API_URL}/imports/confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_no: getUserNo(),
                file_name: previewFileName,
                records,
            }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || "Import failed.");
        }
        reviewStatus.textContent = `${result.imported} records imported with balanced journal entries.`;
        reviewStatus.className = "status success";
        confirmButton.textContent = "Imported";
        window.opener?.postMessage({ type: "records-imported" }, "*");
        window.setTimeout(() => window.close(), 1200);
    } catch (error) {
        reviewStatus.textContent = error.message;
        reviewStatus.className = "status error";
        confirmButton.disabled = false;
    }
}

function openPinModal() {
    const records = collectAndValidate();
    if (!records) return;
    pinDigits.forEach((input) => { input.value = ""; });
    pinStatus.textContent = "";
    pinModal.hidden = false;
    pinDigits[0].focus();
}

function closePinModal() {
    pinModal.hidden = true;
    pinStatus.textContent = "";
}

async function verifyPinAndImport() {
    const pin = pinDigits.map((input) => input.value).join("");
    if (!/^\d{4}$/.test(pin)) {
        pinStatus.textContent = "Enter your complete 4-digit MPIN.";
        return;
    }

    verifyPinButton.disabled = true;
    pinStatus.textContent = "Verifying...";
    try {
        const response = await fetch(`${API_URL}/verify-pin/user`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_no: getUserNo(), pin }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || "Incorrect MPIN.");
        }
        closePinModal();
        await confirmImport();
    } catch (error) {
        pinStatus.textContent = error.message;
    } finally {
        verifyPinButton.disabled = false;
    }
}

pinDigits.forEach((input, index) => {
    input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, "").slice(-1);
        if (input.value && index < pinDigits.length - 1) {
            pinDigits[index + 1].focus();
        }
    });
    input.addEventListener("keydown", (event) => {
        if (event.key === "Backspace" && !input.value && index > 0) {
            pinDigits[index - 1].focus();
        }
        if (event.key === "Enter") {
            verifyPinAndImport();
        }
    });
});

zone.addEventListener("click", () => input.click());
input.addEventListener("change", () => extractFile(input.files[0]));
zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("dragging");
});
zone.addEventListener("dragleave", () => zone.classList.remove("dragging"));
zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("dragging");
    extractFile(event.dataTransfer.files[0]);
});
reviewBody.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-row");
    if (!button) return;
    button.closest(".review-row").remove();
    renumberRows();
});
document.getElementById("cancel-review").addEventListener("click", showUploader);
document.getElementById("close-review").addEventListener("click", showUploader);
confirmButton.addEventListener("click", openPinModal);
document.getElementById("cancel-pin").addEventListener("click", closePinModal);
verifyPinButton.addEventListener("click", verifyPinAndImport);
