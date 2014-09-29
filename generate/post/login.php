<?php


if (isset($_POST['user']) && isset($_POST['pass']))
{
  if ($_POST['user']==="user" && $_POST['pass']==="pass") {
    setcookie("loggedin", "OK", time()+3600);
    header("Location: http://examples.scrapybook.com/post/data.php");
    die();
  }
}

// On error clear success
setcookie("loggedin", "", time()-3600);
header("Location: http://examples.scrapybook.com/post/error.html");

