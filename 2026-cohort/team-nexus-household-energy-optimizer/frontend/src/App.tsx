import { Route, Routes } from "react-router-dom";
import "./App.css";
import { Layout } from "./Layout";
import { Home } from "./pages/Home";
import { Simulator } from "./pages/Simulator";
import { ScoreBreakdown } from "./pages/ScoreBreakdown";
import { EnergyHogs } from "./pages/EnergyHogs";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="simulator" element={<Simulator />} />
        <Route path="score" element={<ScoreBreakdown />} />
        <Route path="hogs" element={<EnergyHogs />} />
      </Route>
    </Routes>
  );
}

export default App;
