<?php

$nonce = rand();
setcookie("cookie", $nonce, time() + (86400 * 30), "/");

?>

<!DOCTYPE html>
<head>
  <meta charset="utf-8">
  <title>Welcome</title>
</head>
<body>
  <h1>Welcome, please login</h1>
  <form method="post" action="nonce-login.php">
    <p><input type="text" name="user" value="" placeholder="Username"></p>
    <p><input type="password" name="pass" value="" placeholder="Password"></p>
    <p class="submit"><input type="submit" name="commit" value="Login"></p>
    <input type="hidden" name="nonce" value="<?= $nonce ?>" />
  </form>
</body>

<p>Post example. For more information: <a href="http://scrapybook.com">scrapybook.com</a></p>
</html>

