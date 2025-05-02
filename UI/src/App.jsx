import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button";
import { Mail } from "lucide-react";

function App() {
  return (
    <div className="flex flex-col items-center justify-center min-h-svh">
      <Button variant={"default"}>
        <Mail /> Login with email
      </Button>
    </div>
  );
}

export default App;
