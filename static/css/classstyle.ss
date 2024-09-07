
body{
  font-size: 16px;
  background-image: url(background.jpg) no-repeat fixed center;
  min-height: 100vh;
}

* {box-sizing: border-box;}

.sidebar{
  background: rgba(28, 28, 38, 0.7);
  color: #fff;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  position: fixed;
  top: 0;
  left: 0;
  width: 15em;
  height: 100%;
  overflow-y: hidden;
}

.sidebar ::-webkit-scrollbar {
width: 5px;
}
.sidebar ::-webkit-scrollbar-track {
background: transparent;
}


.sidebar ::-webkit-scrollbar-thumb {
background: #2a2f44;
  border-radius: 10px;
}

.sidebar > div {
  height: 100%;
  overflow-y: scroll;
  padding: 17em 1em 1.7em 1em;
}

.sidebar a {
  text-decoration: none;
}

.sidebar ul{
  margin: 0;
  padding: 0;
  list-style-type: none;
}

.sidebar small{
  color: #ccc;
}

.brand{
display: block;
  font-size: 1.5em;
  color: #fff;
  font-weight: 600;
}

.menu-heading{
  padding: 1em;
  margin: 2em 0 0.5em 0;
  display: block;
}

.sidebar ul{
  padding-bottom: 1.5em;
}

.sidebar li a{
  color: #ccc;
  display: flex;
  justify-content: start;
  align-items: center;
  padding: 1em;
  border-radius: 0.8em;
  transition: 0.3s;
}

.tools li a:hover{
  background: #1bd030;
  color: #fff;
}

.sidebar ul .material-icons-outlined{
  font-size: 1.6em;
  margin-right: 0.5em;
}

hr {
  border: 1px #2a2f44 solid;
  width: 90%;
  margin: 0 auto;
}

.notifications li a{
  justify-content: space-between;
}

.notifications li a div{
  display: flex;
  justify-content: start;
  align-items: start;
}

.notifcations li a:hover{
  color: #fff;
}

.badge {
  background: #1bd030;
  border-radius: 50%;
  width: 1.8em;
  height: 1.8em;
  text-align: center;
  line-height: 20px;
  color: #fff;
  font-size: 0.7em;
}

.profile{
  padding: 1.7em 1em 3.7em 1em;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile img{
  width: 2.5em;
  height: 2.5em;
  border-radius: 50%;
  display: inline-block;
  text-align: center;
}

.profile h4{
  margin: 0 0 0.5em 0;
}

@media screen and (max-width: 800px) {
  .sidebar {
    width: 4.5em;
    font-size: 14px;
    text-align: center;
  }
  .sidebar > div{
    padding: 1.7em 0.3em 1.7em 0.3em;
  }
  .sidebar span:not(.material-icons-outlined), .profile div, .profile span{
    display: none;
  }
  .menu-heading, .profile{
    margin-top: 0;
  }
  .profile {
    justify-content: center;
  }
}