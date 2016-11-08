(function () {
'use strict';

var RE = /\[(.+)\](.+?)\[\/\1\]/;

var commands = {
  "b": function(data) {
    var b = document.createElement("b");
    b.appendChild(parseString(data));
    return b;
  },
  "img": function(data) {
    var a = document.createElement("a");
    var img = document.createElement("img");
    img.src = data;
    a.href = data;
    a.target = "_blank";
    a.appendChild(img);
    return a;
  }
};

function getColor(str) {
  var number = 0;
  for(var i=0; i<str.length; i++) {
    number += str.charCodeAt(i);
  }
  return "#" + (number % 14).toString(16) + (number % 15).toString(16) + (number % 16).toString(16);
}

function parseString(message) {
  var bits = message.split(RE);
  var msgElement = document.createElement("span");
  for(var i=0; i<bits.length; i+=3) {
    var textNode = bits[i];
    var command = bits[i+1];
    var string = bits[i+2];
    if (textNode) {
      msgElement.appendChild(document.createTextNode(textNode));
    }
    if(command) {
      console.log(command, string)
      msgElement.appendChild(commands[command](string));
    }
  }
  return msgElement;
}

Defiler.prototype.handleChat = function (data) {
  console.log(data);
  if(data.channel == "#main") {
    var element = self.elMainChatMessages;
  } else {
    var element = self.elStreamChatMessages;
  }

  var msgElement = document.createElement('div');
  var userElement = document.createElement('span');
  var textElement = parseString(data.message);
  userElement.appendChild(document.createTextNode(data.nickname + ": "));
  userElement.style.color = getColor(data.nickname);
  msgElement.appendChild(userElement);
  msgElement.appendChild(textElement);
  element.insertBefore(msgElement, element.firstChild);
};

})();
