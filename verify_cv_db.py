import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from database import Database

def verify():
    db = Database()
    print("Testing save_cv...")
    
    # Create a dummy file
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    test_file_path = os.path.join(uploads_dir, "test_cv.pdf")
    
    with open(test_file_path, "w") as f:
        f.write("dummy content")

    try:
        if db.save_cv("Test CV", test_file_path):
            print("save_cv success")
        else:
            print("save_cv failed")
            return

        print("Testing get_all_cvs...")
        cvs = db.get_all_cvs()
        print(f"Found {len(cvs)} CVs")
        found = False
        target_id = None
        for cv in cvs:
            # cv: id, name, filename, created_at
            print(f" - {cv}")
            if cv[1] == "Test CV" and cv[2] == test_file_path:
                found = True
                target_id = cv[0]

        if found:
            print("CV found in DB")
        else:
            print("CV not found in DB")
            return

        if target_id:
            print(f"Testing delete_cv for ID {target_id}...")
            if db.delete_cv(target_id):
                print("delete_cv success")
            else:
                print("delete_cv failed")
                return
                
            # Verify deletion
            cvs = db.get_all_cvs()
            if any(c[0] == target_id for c in cvs):
                print("Error: CV still exists after deletion")
            else:
                print("Verification: CV deleted from DB")
                
    finally:
        # Clean up file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print("Cleaned up test file")

if __name__ == "__main__":
    verify()
