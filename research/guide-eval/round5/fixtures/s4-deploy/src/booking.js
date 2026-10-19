// Class booking widget: shows the next slots and a WhatsApp link.
(function () {
  var slots = [
    { day: "sábado", time: "10:00", seats: 2 },
    { day: "martes", time: "18:30", seats: 4 }
  ];
  var root = document.getElementById("booking");
  if (!root) return;
  var html = "<h2>Próximas clases</h2><ul>";
  slots.forEach(function (s) {
    html += "<li>" + s.day + " " + s.time + " · " + s.seats + " lugares</li>";
  });
  html += "</ul><a href='https://wa.me/5491100000000?text=Hola'><button>Reservar por WhatsApp</button></a>";
  root.innerHTML = html;
})();
