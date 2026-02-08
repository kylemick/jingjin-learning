import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import AgentChat from './pages/AgentChat';
import TimeCompass from './pages/TimeCompass';
import ChoiceNavigator from './pages/ChoiceNavigator';
import ActionWorkshop from './pages/ActionWorkshop';
import LearningDojo from './pages/LearningDojo';
import ThinkingForge from './pages/ThinkingForge';
import TalentGrowth from './pages/TalentGrowth';
import ReviewHub from './pages/ReviewHub';
import Profile from './pages/Profile';
import QuestionBank from './pages/QuestionBank';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/journey" element={<AgentChat />} />
          <Route path="/time-compass" element={<TimeCompass />} />
          <Route path="/choice-navigator" element={<ChoiceNavigator />} />
          <Route path="/action-workshop" element={<ActionWorkshop />} />
          <Route path="/learning-dojo" element={<LearningDojo />} />
          <Route path="/thinking-forge" element={<ThinkingForge />} />
          <Route path="/talent-growth" element={<TalentGrowth />} />
          <Route path="/review-hub" element={<ReviewHub />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/question-bank" element={<QuestionBank />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
