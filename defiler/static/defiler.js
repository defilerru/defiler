'use strict';

var Defiler = function() {
  var self = this;
  var schema = location.protocol == 'https:' ? 'wss://' : 'ws://';
  var elements = ["elOnline", "elAuthInfo", "elMainDiv",
                  "elMainChatInput",
                  "elMainChatMessages",
                  "elStreamChatInput",
                  "elStreamChatMessages",
                  "elStreamChat",
                  "elStreamChatTitle",
                  "elDisplayStreams"
  ];

  for(var i=0; i<elements.length; i++) {
    self[elements[i]] = document.getElementById(elements[i]);
  }
  self.elStreams = document.createElement("div");

  self.currentStream = null;
  self.online = false;

  self.elAuthForm = document.forms["auth"];

  self.elStreams.setAttribute("class", "activeStreams");

  var eventHandler = {
    LOGIN: function(e) {
      if(e.status === "OK") {
        self.elAuthInfo.innerHTML = "logout " + e.username;
        self.hide(self.elAuthForm);
        self.unhide(self.elAuthInfo, "inline");
      }
    },
    LOGOUT: function(e) {
      self.unhide(self.elAuthForm, "inline");
      self.hide(self.elAuthInfo);
    },
    CHAT: function(e) {
      var element = e.channel.length === 0 ? self.elChatMessages : self.elStreamChatMessages;
      self.handleChat(e);
    },
    STREAM: function(e) {
      self.streamUpdate(e);
    },
    STREAM_OFFLINE: function (e) {
      self.streamOff(e);
    },
    USER_ONLINE: function(e) {
    },
    USER_OFFLINE: function(e) {
    },

  };

  function connectWS() {
    self.ws = new WebSocket(schema + window.location.host + "/wsapi");
    self.ws.onmessage = function(e) {
      console.log(e.data);
      var msg = JSON.parse(e.data);
      eventHandler[msg[0]](msg[1]);
    };
    self.ws.onopen = function(e) {
      self.setOnline();
      self.sendWS(["join", {"channel": "#main"}]);
    };
    self.ws.onclose = function(e) {
      self.setOffline();
      self.cls();
      window.setTimeout(connectWS, 5000);
    }
  }

  self.elAuthForm["password"].addEventListener("keyup", function(e) {
    if(e.keyCode === 13) {
      self.login();
    }
  });
  self.elMainChatInput.addEventListener("keyup", function(e) {
    if(e.keyCode === 13 && self.elMainChatInput.value.length > 0) {
      self.chat("#main", self.elMainChatInput);
    }
  });
  self.elStreamChatInput.addEventListener("keyup", function(e) {
    if(e.keyCode === 13 && self.elStreamChatInput.value.length > 0) {
      self.chat(self.currentStream, self.elStreamChatInput);
    }
  });
  self.elAuthInfo.addEventListener("click", function(e) {
    self.logout();
  });
  self.elDisplayStreams.addEventListener("click", function (e) {
    self.displayStreams();
  });
  connectWS();
};

Defiler.prototype.setOffline = function () {
  this.elOnline.style.color = "red";
}

Defiler.prototype.setOnline = function () {
  this.elOnline.style.color = "green";
}

Defiler.prototype.hide = function (element) {
  element.style.visibility = "hidden";
  element.style.display = "none";
};

Defiler.prototype.unhide = function (element, display) {
  element.style.visibility = "visible";
  element.style.display = display;
};

Defiler.prototype.removeChildren = function (element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
};

Defiler.prototype.cls = function () {
  this.removeChildren(this.elMainDiv);
};

Defiler.prototype.sendWS = function (data) {
  this.ws.send(JSON.stringify(data));
};

Defiler.prototype.login = function() {
  this.sendWS(['login', {
    username: this.elAuthForm.username.value,
    password: this.elAuthForm.password.value}]);
  this.elAuthForm.password.value = "";
};

Defiler.prototype.logout = function () {
  this.sendWS(['logout', {}]);
}

Defiler.prototype.chat = function(channel, input) {
  this.sendWS(['chat', {
    channel: channel,
    message: input.value}]);
  input.value = "";
};
