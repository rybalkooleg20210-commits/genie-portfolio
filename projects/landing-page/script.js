(function () {
  var form = document.getElementById("booking-form");
  var msg = document.getElementById("form-msg");
  if (!form || !msg) return;

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var data = new FormData(form);
    var name = String(data.get("name") || "").trim() || "гість";
    var date = String(data.get("date") || "обрану дату");
    var guests = String(data.get("guests") || "2");
    msg.hidden = false;
    msg.textContent =
      "Дякуємо, " + name + "! Демо-запит на " + guests + " гостей (" + date + ") прийнято локально. Нічого не відправлено.";
    form.reset();
  });
})();
