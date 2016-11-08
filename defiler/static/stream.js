(function () {
'use strict';

var providers = {
  twitch: function(slug) {
    var iframe = document.createElement("iframe");
    iframe.src = "https://player.twitch.tv/?channel=" + slug;
    iframe.setAttribute("allowfullscreen", "true");
    iframe.setAttribute("frameborder", "0");
    return iframe;
  },
  afreeca: function(slug) {
    var iframe = document.createElement("iframe");
    iframe.src = "http://play.afreeca.com/" + slug + "/embed";
    iframe.frameborder = "0";
    return iframe;
  }
};

function getStreamDiv(stream) {
  var self = this;
  var div = document.createElement("div");
  var innerDiv = document.createElement("div");
  innerDiv.appendChild(document.createTextNode(stream.slug));
  div.appendChild(innerDiv);
  var img = document.createElement("img");
  img.src = stream.preview;
  div.appendChild(img);
  div.id = "stream_" + stream.provider + stream.slug;
  return div;
}

Defiler.prototype.watchStream = function (provider, slug) {
  location.hash = "#/stream/" + provider + "/" + slug;
  this.cls();
  console.log(this.currentStream);
  if (this.currentStream) {
    this.sendWS(["leave", {channel: this.currentStream}]);
  }
  this.currentStream = "#" + provider + "/" + slug;
  console.log(this.currentStream);
  this.elStreamChatTitle.textContent = this.currentStream;
  this.elMainDiv.appendChild(providers[provider](slug));
  this.removeChildren(this.elStreamChatMessages);
  this.unhide(this.elStreamChat, "block");
  this.sendWS(["join", {"channel": this.currentStream}]);
}

Defiler.prototype.displayStreams = function () {
  location.hash = "#streams"
  this.cls();
  this.elMainDiv.appendChild(this.elStreams);
}

Defiler.prototype.streamUpdate = function (e) {
  var self = this;
  var div = getStreamDiv(e);
  console.log(div);
  div.addEventListener("click", function() {
    self.watchStream(e.provider, e.slug);
  });
  self.elStreams.appendChild(div);
}

Defiler.prototype.streamOff = function(e) {
  var div = document.getElementById("stream_" + e.provider + e.slug);
  self.elStreams.removeChild(div);
}

Defiler.prototype.refreshStreamPreviews = function () {
  var self=this;
  for(var i=0; i<self.elDisplayStreams.childNodes.length; i++) {
    console.log(self.elDisplayStreams.childNodes[i]);
  }
}

})();
