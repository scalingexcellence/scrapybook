<?php


if (!isset($_COOKIE['loggedin']) || $_COOKIE['loggedin']!=="OK")
{
  // On error clear success
  setcookie("loggedin", "", time()-3600);
  header("Location: http://examples.scrapybook.com/post/error.html");
  die();
}


?><!DOCTYPE html>
<head>
  <meta charset="utf-8">
  <title>Congratulations</title>
</head>
<body>
  <h1>Here are your links</h1>
  <ul class="links">
    <li><a href="http://s3.amazonaws.com/scrapybook/properties/property_000000.html">link1</a></li>
    <li><a href="http://s3.amazonaws.com/scrapybook/properties/property_000001.html">link2</a></li>
    <li><a href="http://s3.amazonaws.com/scrapybook/properties/property_000002.html">link3</a></li>
  </ul>

<p>Post example. For more information: <a href="http://scrapybook.com">scrapybook.com</a></p>
</body>
</html>

