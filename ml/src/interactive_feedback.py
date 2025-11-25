"""
Interactive feedback session for the Vector DB Classifier.
Allows users to test error classification and provide corrections.
"""

from search_engines import initialize_vector_db


def run_interactive_session(kb=None):
    """Run interactive feedback session with the vector database."""
    if kb is None:
        kb = initialize_vector_db()

    print("\nVector DB Classifier is Live!")
    print("Type an error message to classify it. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input(">> Enter Error Log: ").strip()
        except EOFError:
            break
            
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
        
        if not user_input:
            continue

        # Search for matching documentation
        result = kb.search(user_input)
        
        # Display the result
        print(f"\nAI Suggestion:")
        print(f"\t*Doc Path:\t{result['doc_path']}")
        print(f"\t*Source:\t{result['source']}")
        if 'confidence' in result:
             print(f"\t*Confidence:\t{result['confidence']}")
        
        # Feedback mechanism
        user_feedback = input("\nIs this correct? (y/n): ").lower().strip()
        
        if user_feedback == 'y':
            print("Excellent. No changes needed.")
        
        elif user_feedback == 'n':
            print("Okay, let's fix it.")
            correct_path = input("Enter the correct documentation path (e.g., docs/...): ").strip()
            
            if correct_path:
                # Teach the system the correct answer
                kb.teach_system(user_input, correct_path)
                print("Learned! Next time I'll remember this.")
            else:
                print("No path provided. Skipping update.")
        
        print("-" * 40)


if __name__ == "__main__":
    run_interactive_session()
