document.addEventListener("DOMContentLoaded", () => {
  const tablaHistorial = document.querySelector("#tablaHistorial tbody");

  async function cargarHistorial() {
    try {
      const res = await fetch("/api/products/stock-history");
      const data = await res.json();

      tablaHistorial.innerHTML = "";

      data.forEach(entry => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${entry.product_name || entry.product_id}</td>
          <td style="color:${entry.change > 0 ? 'green' : 'red'};">
            ${entry.change > 0 ? "+" : ""}${entry.change}
          </td>
          <td>${entry.reason}</td>
          <td>${new Date(entry.timestamp).toLocaleString()}</td>
        `;

        tablaHistorial.appendChild(fila);
      });
    } catch (err) {
      document.getElementById("messageHistorial").textContent = "Error al cargar historial: " + err.message;
    }
  }

  // Puedes hacer que se cargue automáticamente al cambiar a esa pestaña
  window.mostrarSeccion = function (id) {
    document.querySelectorAll("section").forEach(sec => sec.style.display = "none");
    document.getElementById(id).style.display = "block";

    if (id === "historial") {
      cargarHistorial();
    }
  };
});
