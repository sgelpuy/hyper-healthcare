// ---------- 공통 ----------

const CATEGORY_STYLE = {
  "정상": "good",
  "적정": "good",
  "저체중": "info",
  "우수": "info",
  "주의": "warn",
  "과체중": "warn",
  "공복혈당장애": "warn",
  "부족": "warn",
  "과다": "warn",
  "비만": "bad",
  "고혈압": "bad",
  "당뇨 의심": "bad",
};

function badge(text) {
  const cls = CATEGORY_STYLE[text] || "info";
  return `<span class="badge badge-${cls}">${text}</span>`;
}

async function api(path, options) {
  const res = await fetch(path, options);
  let body = null;
  try {
    body = await res.json();
  } catch (e) {
    body = null;
  }
  if (!res.ok) {
    const detail = body && body.detail ? body.detail : res.status;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

// ---------- 탭 전환 ----------

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

function switchTab(name) {
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${name}`));
}

// ---------- 기록 입력 / 수정 ----------

let editingId = null;
const recordForm = document.getElementById("record-form");
const submitBtn = document.getElementById("record-submit-btn");
const cancelBtn = document.getElementById("record-cancel-btn");
const inputTitle = document.getElementById("input-title");

function readRecordForm(form) {
  return {
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
}

function startEdit(record) {
  editingId = record.id;
  const form = recordForm;
  form.user.value = record.user;
  form.date.value = record.date;
  form.weight.value = record.weight;
  form.height.value = record.height;
  form.systolic.value = record.systolic;
  form.diastolic.value = record.diastolic;
  form.blood_sugar.value = record.blood_sugar;
  form.steps.value = record.steps;
  form.sleep_hours.value = record.sleep_hours;
  form.memo.value = record.memo;

  inputTitle.textContent = `기록 수정 (id: ${record.id})`;
  submitBtn.textContent = "수정 완료";
  cancelBtn.style.display = "inline-block";
  switchTab("input");
}

function cancelEdit() {
  editingId = null;
  recordForm.reset();
  inputTitle.textContent = "기록 입력";
  submitBtn.textContent = "등록";
  cancelBtn.style.display = "none";
}

cancelBtn.addEventListener("click", cancelEdit);

recordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = readRecordForm(e.target);

  try {
    if (editingId !== null) {
      await api(`/records/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    } else {
      await api("/records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    }
    const savedUser = data.user;
    cancelEdit();
    document.getElementById("list-user").value = savedUser;
    switchTab("list");
    await loadList(savedUser);
  } catch (err) {
    alert("저장 실패: " + err.message);
  }
});

// ---------- 기록 조회 ----------

function renderRecordsTable(container, records) {
  if (!records.length) {
    container.innerHTML = '<p class="empty">기록이 없습니다.</p>';
    return;
  }

  const rows = records
    .map(
      (r) => `
      <tr>
        <td>${r.id}</td>
        <td>${r.user}</td>
        <td>${r.date}</td>
        <td>${r.weight}</td>
        <td>${r.bmi} ${badge(r.bmi_category)}</td>
        <td>${r.systolic}/${r.diastolic} ${badge(r.bp_category)}</td>
        <td>${r.blood_sugar} ${badge(r.sugar_category)}</td>
        <td>${r.steps} ${badge(r.steps_grade)}</td>
        <td>${r.sleep_hours}h ${badge(r.sleep_category)}</td>
        <td>${r.warnings.map((w) => `<span class="badge badge-bad">${w}</span>`).join("") || "-"}</td>
        <td>
          <button class="action-btn secondary" onclick='editRecordById(${r.id})'>수정</button>
          <button class="action-btn danger" onclick='deleteRecordById(${r.id})'>삭제</button>
        </td>
      </tr>`
    )
    .join("");

  container.innerHTML = `
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>사용자</th><th>날짜</th><th>체중</th><th>BMI</th>
            <th>혈압</th><th>혈당</th><th>걸음수</th><th>수면</th><th>경고</th><th>액션</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

let currentListRecords = [];

async function loadList(user) {
  const url = user ? `/records?user=${encodeURIComponent(user)}` : "/records";
  const data = await api(url);
  currentListRecords = data.records;
  renderRecordsTable(document.getElementById("list-result"), data.records);
}

function editRecordById(id) {
  const record = currentListRecords.find((r) => r.id === id);
  if (record) startEdit(record);
}

async function deleteRecordById(id) {
  if (!confirm(`기록 ${id}번을 삭제할까요?`)) return;
  try {
    await api(`/records/${id}`, { method: "DELETE" });
    await loadList(document.getElementById("list-user").value);
  } catch (err) {
    alert("삭제 실패: " + err.message);
  }
}

document.getElementById("list-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await loadList(document.getElementById("list-user").value);
});

// ---------- 기간 검색 ----------

document.getElementById("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const start = document.getElementById("search-start").value;
  const end = document.getElementById("search-end").value;
  const user = document.getElementById("search-user").value;

  const params = new URLSearchParams({ start, end });
  if (user) params.set("user", user);

  try {
    const data = await api(`/search?${params.toString()}`);
    currentListRecords = data.records;
    renderRecordsTable(document.getElementById("search-result"), data.records);
  } catch (err) {
    alert("검색 실패: " + err.message);
  }
});

// ---------- 통계 ----------

document.getElementById("stats-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const user = document.getElementById("stats-user").value;
  const url = user ? `/stats?user=${encodeURIComponent(user)}` : "/stats";
  const container = document.getElementById("stats-result");

  try {
    const data = await api(url);
    if (!data.count) {
      container.innerHTML = '<p class="empty">통계를 계산할 기록이 없습니다.</p>';
      return;
    }
    const cards = [
      ["기록 수", data.count],
      ["평균 체중", `${data.avg_weight} kg`],
      ["평균 수축기", data.avg_systolic],
      ["평균 이완기", data.avg_diastolic],
      ["평균 혈당", data.avg_blood_sugar],
      ["평균 걸음수", data.avg_steps],
      ["평균 수면", `${data.avg_sleep_hours} h`],
    ];
    container.innerHTML = `
      <div class="stat-cards">
        ${cards
          .map(([label, value]) => `<div class="stat-card"><div class="label">${label}</div><div class="value">${value}</div></div>`)
          .join("")}
      </div>`;
  } catch (err) {
    alert("통계 조회 실패: " + err.message);
  }
});

// ---------- 주간 리포트 ----------

document.getElementById("weekly-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const user = document.getElementById("weekly-user").value;
  const container = document.getElementById("weekly-result");

  try {
    const data = await api(`/weekly-report?user=${encodeURIComponent(user)}`);
    const changeText =
      data.change === null
        ? "비교 불가 (데이터 부족)"
        : data.change > 0
        ? `+${data.change} kg 증가`
        : data.change < 0
        ? `${data.change} kg 감소`
        : "변화 없음";

    container.innerHTML = `
      <div class="stat-cards">
        <div class="stat-card"><div class="label">이번 주 평균 체중</div><div class="value">${data.this_week_avg_weight ?? "-"}</div></div>
        <div class="stat-card"><div class="label">지난 주 평균 체중</div><div class="value">${data.last_week_avg_weight ?? "-"}</div></div>
        <div class="stat-card"><div class="label">변화</div><div class="value">${changeText}</div></div>
      </div>`;
  } catch (err) {
    alert("주간 리포트 조회 실패: " + err.message);
  }
});

// ---------- 목표 관리 ----------

document.getElementById("goal-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = {
    user: form.user.value,
    target_weight: form.target_weight.value ? parseFloat(form.target_weight.value) : null,
    target_systolic: form.target_systolic.value ? parseInt(form.target_systolic.value) : null,
    target_diastolic: form.target_diastolic.value ? parseInt(form.target_diastolic.value) : null,
  };
  const resultEl = document.getElementById("goal-save-result");

  try {
    await api("/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    resultEl.textContent = `${data.user}님의 목표가 저장되었습니다.`;
  } catch (err) {
    resultEl.textContent = "저장 실패: " + err.message;
  }
});

document.getElementById("goal-progress-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const user = document.getElementById("goal-progress-user").value;
  const container = document.getElementById("goal-progress-result");

  try {
    const data = await api(`/goals/${encodeURIComponent(user)}/progress`);
    if (data.message) {
      container.innerHTML = `<p class="empty">${data.message}</p>`;
      return;
    }
    const cards = [];
    if (data.weight_progress_pct !== undefined) {
      cards.push(["체중 달성률", `${data.weight_progress_pct}%`]);
      cards.push(["현재 체중 / 목표", `${data.current_weight} / ${data.target_weight} kg`]);
    }
    if (data.bp_achieved !== undefined) {
      cards.push(["혈압 목표 달성", data.bp_achieved ? "달성" : "미달성"]);
      cards.push(["현재 혈압 / 목표", `${data.current_bp} / ${data.target_bp}`]);
    }
    container.innerHTML = `
      <div class="stat-cards">
        ${cards
          .map(([label, value]) => `<div class="stat-card"><div class="label">${label}</div><div class="value">${value}</div></div>`)
          .join("")}
      </div>`;
  } catch (err) {
    container.innerHTML = `<p class="empty">조회 실패: ${err.message}</p>`;
  }
});

// ---------- 초기 로드 ----------

loadList("");
