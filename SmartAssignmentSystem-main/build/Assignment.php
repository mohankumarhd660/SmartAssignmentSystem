<?php
$host = "localhost";
$user = "root"; // change if needed
$pass = "";
$dbname = "student_db";

$conn = new mysqli($host, $user, $pass, $dbname);
if ($conn->connect_error) {
    die("DB Connection Failed!");
}

if (isset($_POST['add_student'])) {
    $name = $_POST['name'];
    $roll = $_POST['roll'];
    $conn->query("INSERT INTO students (name, roll) VALUES ('$name', '$roll')");
}

if (isset($_POST['add_assignment'])) {
    $title = $_POST['title'];
    $desc = $_POST['desc'];
    $due = $_POST['due'];
    $conn->query("INSERT INTO assignments (title, description, due_date) VALUES ('$title','$desc','$due')");
}

if (isset($_POST['submit_status'])) {
    $student = $_POST['student'];
    $assignment = $_POST['assignment'];
    $status = $_POST['status'];
    $today = date("Y-m-d");
    
    $conn->query("INSERT INTO submissions (student_id, assignment_id, status, submitted_on)
                  VALUES ($student, $assignment, '$status', '$today')");
}
?>

<!DOCTYPE html>
<html>
<head>
<title>Student Assignment System</title>
<style>
body { font-family: Arial; background:#e8f7fa; }
.container { width: 700px; margin: auto; padding: 20px; background:white;
             border-radius: 10px; margin-top:30px; box-shadow: 0 0 10px #ccc; }
input, select, textarea { width:100%; padding:8px; margin:5px 0;
                          border-radius:5px; border:1px solid #666; }
button { background:#007bff; color:white; padding:8px 20px; border:none;
         border-radius:5px; cursor:pointer; margin-top:5px; }
h2 { background:#18a2b8; color:white; padding:10px; }
table { width:100%; border-collapse:collapse; margin-top:10px; }
th, td { border:1px solid #888; padding:8px; text-align:center; }
th { background:#007bff; color:white; }
</style>
</head>
<body>

<div class="container">
<h2>Add Student</h2>
<form method="POST">
<input type="text" name="name" placeholder="Student Name" required>
<input type="text" name="roll" placeholder="Roll Number" required>
<button type="submit" name="add_student">Add Student</button>
</form>

<h2>Add Assignment</h2>
<form method="POST">
<input type="text" name="title" placeholder="Assignment Title" required>
<textarea name="desc" placeholder="Description"></textarea>
<input type="date" name="due" required>
<button type="submit" name="add_assignment">Add Assignment</button>
</form>

<h2>Submit Assignment Status</h2>
<form method="POST">
<select name="student" required>
<option value="">Select Student</option>
<?php
$stud = $conn->query("SELECT * FROM students");
while($s = $stud->fetch_assoc()) {
    echo "<option value='{$s['id']}'>{$s['name']} ({$s['roll']})</option>";
}
?>
</select>

<select name="assignment" required>
<option value="">Select Assignment</option>
<?php
$assign = $conn->query("SELECT * FROM assignments");
while($a = $assign->fetch_assoc()) {
    echo "<option value='{$a['id']}'>{$a['title']}</option>";
}
?>
</select>

<select name="status">
<option value="Submitted">Submitted</option>
<option value="Pending">Pending</option>
</select>

<button type="submit" name="submit_status">Save Status</button>
</form>

<h2>Assignment Status</h2>
<table>
<tr>
<th>Student</th><th>Assignment</th><th>Status</th><th>Date</th>
</tr>
<?php
$res = $conn->query("SELECT s.name, a.title, sub.status, sub.submitted_on 
                     FROM submissions sub 
                     JOIN students s ON sub.student_id=s.id 
                     JOIN assignments a ON sub.assignment_id = a.id");
while($row = $res->fetch_assoc()) {
    echo "<tr>
    <td>{$row['name']}</td>
    <td>{$row['title']}</td>
    <td>{$row['status']}</td>
    <td>{$row['submitted_on']}</td>
    </tr>";
}
?>
</table>
</div>

</body>
</html>
