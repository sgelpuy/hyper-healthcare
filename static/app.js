document.getElementById("record-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = {
    user: form.user.value,
    date: form.date.value,
    weight: parseFloat(form.weight.value),
    height: parseFloat(form.height.value),
    systolic: parseInt(form.systolic.value),
    diastolic: parseInt(form.diastolic.value),
    blood_sugar: parseInt(form.blood_sugar.value),
    steps: form.steps.value ? parseInt(form.steps.value) : 0,
    sleep_hours: form.sleep_hours.value ? parseFloat(form.sleep_hours.value) : 0,
    memo: form.memo.value,
  };

  const res = await fetch("/records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (res.ok) {
    form.reset();
    loadRecords(data.user);
  } else {
    alert("등록 실패: " + res.status);
  }
});



async function loadRecords(user) {
  const url = user ? `/records?user=${encodeURIComponent(user)}` : "/records";
  const res = await fetch(url);
  const data = await res.json();

  const tbody = document.querySelector("#record-table tbody");
  tbody.innerHTML = "";
  data.records.forEach((r) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${r.date}</td>
      <td>${r.weight}</td>
      <td>${r.bmi}</td>
      <td>${r.bmi_category}</td>
      <td>${r.bp_category}</td>
      <td>${r.sugar_category}</td>
      <td>${r.warnings.join(", ")}</td>
    `;
    tbody.appendChild(row);
  });
}

document.getElementById("search-btn").addEventListener("click", () => {
  loadRecords(document.getElementById("user-filter").value);
});

loadRecords();  // 페이지 처음 열릴 때 전체 조회