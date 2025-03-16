const ThesisAnalytics = (function () {
  let designName = "Design";
  let colorCode = "#000000";

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    return parts.length === 2 ? parts.pop().split(";").shift() : null;
  };

  const setCookie = (name, value, days) => {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${value}; expires=${expires}; path=/`;
  };

  const generateUUID = () => {
    return "xxxx-xxxx-4xxx-yxxx-xxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0,
        v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  };

  const showModal = (uuid) => {
    modal = document.createElement("div");
    modal.style =
      "position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.75); display: flex; justify-content: center; align-items: center; z-index: 100;";
    modal.innerHTML = `
              <div style="background-color: white; padding: 20px; border-radius: 10px; text-align: center;">
                  <p>You are viewing <span style="font-weight: 900; font-size: 18px; color: ${colorCode}">${designName}</span>. Please copy this UUID and paste it into the Google Form.</p>
                  <input type="text" value="${uuid}" readonly style="text-align: center; margin-bottom: 10px; width: 300px; padding: 5px; border-radius: 10px; border: solid 1px rgba(0, 0, 0, 0.5); font-size: 16px;">
                  <br>
                  <button id="copyButton">Copy</button>
                  <button onclick="this.parentNode.parentNode.style.display = 'none';">Close</button>
              </div>
          `;
    document.body.appendChild(modal);

    document.getElementById("copyButton").addEventListener("click", () => {
      navigator.clipboard.writeText(uuid);
    });
  };

  const showStickyBox = (uuid) => {
    const stickyBox = document.createElement("div");
    stickyBox.style =
      "position: fixed; bottom: 0; left: 0; width: 100%; background-color: #f9f9f9; padding: 10px; text-align: center; border-top: 1px solid #ccc; z-index: 50;";
    stickyBox.innerHTML = `
              You are viewing <span style="font-weight: 900; font-size: 18px; color: ${colorCode}">${designName}</span>. Your Session UUID: ${uuid} <button style="padding: 5px 10px; margin: 0 10px; border-style: none; border: solid 2px rgba(0, 0, 0, 0.75); background: white; cursor: pointer; border-radius: 5px;" onclick="navigator.clipboard.writeText('${uuid}');">Copy</button>
          `;
    document.body.appendChild(stickyBox);
  };

  const sendLog = (event, data) => {
    const logData = {
      uuid: getCookie("sessionUUID"),
      design: designName,
      event,
      data,
      timestamp: new Date().toISOString(),
    };

    fetch("https://sayedmahmod.de:8000/log", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(logData),
    }).catch((error) => console.error("Error logging event:", error));
  };

  return {
    init: (design, color) => {
      designName = design;
      colorCode = color || "#000000";
      let uuid = getCookie("sessionUUID");
      if (!uuid) {
        uuid = generateUUID();
        setCookie("sessionUUID", uuid, 30);
        showModal(uuid);
      }

      showStickyBox(uuid);
    },
    log: (event, data) => sendLog(event, data),
  };
})();
