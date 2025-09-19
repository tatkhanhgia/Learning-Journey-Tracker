import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Avatar, AvatarFallback } from './components/ui/avatar';
import { Progress } from './components/ui/progress';
import { toast } from 'sonner';
import { Toaster } from './components/ui/toaster';
import { 
  LogIn, 
  LogOut, 
  Users, 
  BookOpen, 
  MessageSquare, 
  CheckCircle2, 
  Circle,
  Plus,
  Edit3,
  Trash2,
  User,
  ChevronRight,
  ChevronDown,
  ArrowLeft,
  Home,
  Play,
  FlaskConical,
  Share,
  Upload,
  ExternalLink,
  Search,
  Filter,
  FileText,
  Image,
  Video,
  Download
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password
      });
      
      const { access_token, user_info } = response.data;
      setToken(access_token);
      setUser(user_info);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      toast.success(`Chào mừng ${user_info.full_name}!`, {
        duration: 3000,
        position: 'top-center'
      });
      return true;
    } catch (error) {
      console.error('Login error:', error);
      let message = 'Đăng nhập thất bại';
      
      if (error.response?.status === 401) {
        message = error.response?.data?.detail || 'Tên đăng nhập hoặc mật khẩu không đúng';
      } else if (error.response?.status === 500) {
        message = 'Lỗi server, vui lòng thử lại sau';
      } else if (error.code === 'NETWORK_ERROR' || !error.response) {
        message = 'Không thể kết nối đến server';
      }
      
      toast.error(message, {
        duration: 4000,
        position: 'top-center'
      });
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    toast.success('Đã đăng xuất thành công');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component (unchanged)
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogging, setIsLogging] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    
    if (!username || !password) {
      setErrorMessage('Vui lòng nhập đầy đủ thông tin');
      toast.error('Vui lòng nhập đầy đủ thông tin');
      return;
    }

    setIsLogging(true);
    const success = await login(username, password);
    
    if (!success) {
      setErrorMessage('Tên đăng nhập hoặc mật khẩu không đúng');
    } else {
      navigate('/', { replace: true });
    }
    
    setIsLogging(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-8">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-2xl text-slate-800 font-semibold">LearnTrack</CardTitle>
            <CardDescription className="text-slate-600">
              Hệ thống quản lý tiến độ học tập
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Tên đăng nhập</label>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Nhập tên đăng nhập"
                  disabled={isLogging}
                  className="h-11 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Mật khẩu</label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu"
                  disabled={isLogging}
                  className="h-11 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              
              {errorMessage && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600 text-center">{errorMessage}</p>
                </div>
              )}
              
              <Button
                type="submit"
                disabled={isLogging}
                className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white font-medium"
              >
                {isLogging ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Đang đăng nhập...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <LogIn className="w-4 h-4" />
                    Đăng nhập
                  </div>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Breadcrumb Component
const Breadcrumb = ({ items, onNavigate }) => {
  return (
    <nav className="flex items-center space-x-2 text-sm text-slate-600 mb-6">
      <button 
        onClick={() => onNavigate([])}
        className="flex items-center gap-1 hover:text-blue-600 transition-colors"
      >
        <Home className="w-4 h-4" />
        <span>Trang chủ</span>
      </button>
      
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="w-4 h-4" />
          <button
            onClick={() => onNavigate(items.slice(0, index + 1))}
            className={`hover:text-blue-600 transition-colors ${
              index === items.length - 1 ? 'text-slate-800 font-medium' : ''
            }`}
          >
            {item.name}
          </button>
        </React.Fragment>
      ))}
    </nav>
  );
};

// Dashboard Component with Hierarchical Navigation
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [allProgress, setAllProgress] = useState([]);
  const [myProgress, setMyProgress] = useState([]);
  const [notes, setNotes] = useState([]);
  const [structure, setStructure] = useState({ resources: [] });
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedUser, setExpandedUser] = useState(null); // State để track user nào đang được mở rộng
  const [activeTab, setActiveTab] = useState('overview');
  
  // Navigation states
  const [navigationPath, setNavigationPath] = useState([]); // Array of {type: 'resource'|'module'|'session', name: string, data: object}
  const [currentView, setCurrentView] = useState('resources'); // 'resources' | 'modules' | 'sessions'
  const [currentData, setCurrentData] = useState([]);

  // Note dialog states
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [noteForm, setNoteForm] = useState({ resource: '', module: '', session: '', content: '' });
  const [editingNote, setEditingNote] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (preserveNavigation = false) => {
    try {
      setLoading(true);
      const [progressRes, myProgressRes, notesRes, structureRes, usersRes] = await Promise.all([
        axios.get(`${API}/progress`),
        axios.get(`${API}/progress/me`),
        axios.get(`${API}/notes`),
        axios.get(`${API}/structure`),
        axios.get(`${API}/config/users`)
      ]);

      setAllProgress(progressRes.data.progress);
      setMyProgress(myProgressRes.data.progress);
      setNotes(notesRes.data.notes);
      setStructure(structureRes.data);
      setUsers(usersRes.data.users);
      
      // Only set initial current data to resources if we're not preserving navigation
      if (!preserveNavigation) {
        setCurrentData(structureRes.data.resources || []);
      } else {
        // Preserve current navigation by re-applying the navigation path
        refreshCurrentView(structureRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  const refreshCurrentView = (structureData) => {
    // Re-apply current navigation to preserve view after data refresh
    if (navigationPath.length === 0) {
      setCurrentView('resources');
      setCurrentData(structureData.resources || []);
    } else if (navigationPath.length === 1) {
      // Show modules for selected resource
      const resource = structureData.resources.find(r => r.name === navigationPath[0].name);
      setCurrentView('modules');
      setCurrentData(resource ? resource.modules : []);
    } else if (navigationPath.length === 2) {
      // Show sessions for selected module
      const resource = structureData.resources.find(r => r.name === navigationPath[0].name);
      const module = resource ? resource.modules.find(m => m.name === navigationPath[1].name) : null;
      setCurrentView('sessions');
      setCurrentData(module ? module.sessions : []);
    }
  };

  const handleNavigation = (path) => {
    setNavigationPath(path);
    
    if (path.length === 0) {
      // Back to resources
      setCurrentView('resources');
      setCurrentData(structure.resources || []);
    } else if (path.length === 1) {
      // Show modules for selected resource
      const resource = structure.resources.find(r => r.name === path[0].name);
      setCurrentView('modules');
      setCurrentData(resource ? resource.modules : []);
    } else if (path.length === 2) {
      // Show sessions for selected module
      const resource = structure.resources.find(r => r.name === path[0].name);
      const module = resource ? resource.modules.find(m => m.name === path[1].name) : null;
      setCurrentView('sessions');
      setCurrentData(module ? module.sessions : []);
    }
  };

  const handleItemClick = (item) => {
    if (currentView === 'resources') {
      const newPath = [{ type: 'resource', name: item.name, data: item }];
      handleNavigation(newPath);
    } else if (currentView === 'modules') {
      const newPath = [...navigationPath, { type: 'module', name: item.name, data: item }];
      handleNavigation(newPath);
    }
    // Sessions are leaf nodes, no further navigation
  };

  const updateProgress = async (resource, module, session, completed) => {
    try {
      await axios.post(`${API}/progress`, { resource, module, session, completed });
      await fetchData(true); // Preserve navigation when updating progress
      toast.success(completed ? 'Đã đánh dấu hoàn thành' : 'Đã hủy đánh dấu hoàn thành');
    } catch (error) {
      console.error('Failed to update progress:', error);
      toast.error('Không thể cập nhật tiến độ');
    }
  };

  const handleNoteSubmit = async (e) => {
    e.preventDefault();
    if (!noteForm.resource || !noteForm.module || !noteForm.session || !noteForm.content.trim()) {
      toast.error('Vui lòng điền đầy đủ thông tin');
      return;
    }

    try {
      if (editingNote) {
        await axios.put(`${API}/notes/${editingNote.id}`, { content: noteForm.content });
        toast.success('Đã cập nhật ghi chú');
      } else {
        await axios.post(`${API}/notes`, noteForm);
        toast.success('Đã tạo ghi chú mới');
      }
      
      setIsNoteDialogOpen(false);
      setNoteForm({ resource: '', module: '', session: '', content: '' });
      setEditingNote(null);
      await fetchData(true); // Preserve navigation when updating notes
    } catch (error) {
      console.error('Failed to save note:', error);
      toast.error('Không thể lưu ghi chú');
    }
  };

  const deleteNote = async (noteId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa ghi chú này?')) return;

    try {
      await axios.delete(`${API}/notes/${noteId}`);
      toast.success('Đã xóa ghi chú');
      await fetchData(true); // Preserve navigation when deleting notes
    } catch (error) {
      console.error('Failed to delete note:', error);
      toast.error('Không thể xóa ghi chú');
    }
  };

  const calculateProgressPercentage = (userProgress) => {
    let totalSessions = 0;
    let completedSessions = 0;
    
    userProgress.resources.forEach(resource => {
      resource.modules.forEach(module => {
        module.sessions.forEach(session => {
          totalSessions++;
          if (session.completed) {
            completedSessions++;
          }
        });
      });
    });
    
    return totalSessions > 0 ? Math.round((completedSessions / totalSessions) * 100) : 0;
  };

  // Function để toggle dropdown của user
  const toggleUserExpansion = (username) => {
    setExpandedUser(expandedUser === username ? null : username);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-800">LearnTrack</h1>
              <p className="text-sm text-slate-600">Quản lý tiến độ học tập</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="bg-blue-100 text-blue-600 text-sm">
                  {user?.full_name?.charAt(0) || user?.username?.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-slate-700">{user?.full_name}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="text-slate-600 hover:text-slate-800"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Đăng xuất
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 max-w-md">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Tổng quan
            </TabsTrigger>
            <TabsTrigger value="my-progress" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Tiến độ của tôi
            </TabsTrigger>
            <TabsTrigger value="notes" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Ghi chú
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab - All Users Progress với Dropdown */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6">
              <h2 className="text-2xl font-semibold text-slate-800">Tiến độ của tất cả thành viên</h2>
              
              <div className="grid gap-4">
                {allProgress.map((userProgress) => (
                  <Card key={userProgress.username} className="shadow-sm border-slate-200">
                    <CardHeader 
                      className="pb-4 cursor-pointer hover:bg-slate-50 transition-colors"
                      onClick={() => toggleUserExpansion(userProgress.username)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar className="w-10 h-10">
                            <AvatarFallback className="bg-slate-100 text-slate-600">
                              {userProgress.full_name.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <CardTitle className="text-lg text-slate-800">{userProgress.full_name}</CardTitle>
                            <CardDescription>@{userProgress.username}</CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-2xl font-bold text-blue-600">
                              {calculateProgressPercentage(userProgress)}%
                            </div>
                            <div className="text-sm text-slate-500">Hoàn thành</div>
                          </div>
                          {expandedUser === userProgress.username ? (
                            <ChevronDown className="w-5 h-5 text-slate-400" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                      </div>
                      <Progress 
                        value={calculateProgressPercentage(userProgress)} 
                        className="mt-3"
                      />
                    </CardHeader>
                    
                    {/* Chỉ hiển thị progress details khi user được expand */}
                    {expandedUser === userProgress.username && (
                      <CardContent>
                        <div className="space-y-4">
                          {userProgress.resources.map((resource) => (
                            <div key={resource.name}>
                              <h4 className="font-medium text-slate-700 mb-2">{resource.name}</h4>
                              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 ml-4">
                                {resource.modules.map((module) => (
                                  <div key={module.name} className="space-y-1">
                                    <div className="text-sm font-medium text-slate-600">{module.name}</div>
                                    <div className="flex flex-wrap gap-1">
                                      {module.sessions.map((session) => (
                                        <div
                                          key={session.name}
                                          className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                                            session.completed
                                              ? 'bg-green-100 text-green-700'
                                              : 'bg-slate-100 text-slate-600'
                                          }`}
                                        >
                                          {session.type === 'lab' ? (
                                            <FlaskConical className="w-3 h-3" />
                                          ) : (
                                            <Play className="w-3 h-3" />
                                          )}
                                          <span>{session.name}</span>
                                          {session.completed && <CheckCircle2 className="w-3 h-3" />}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* My Progress Tab - Hierarchical Navigation */}
          <TabsContent value="my-progress" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-800">Tiến độ của tôi</h2>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">
                  {myProgress.length > 0 ? calculateProgressPercentage({ resources: myProgress }) : 0}%
                </div>
                <div className="text-sm text-slate-500">Hoàn thành</div>
              </div>
            </div>

            <Breadcrumb items={navigationPath} onNavigate={handleNavigation} />

            <Card className="shadow-sm border-slate-200">
              <CardContent className="p-6">
                {currentView === 'resources' && (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {currentData.map((resource) => (
                      <div
                        key={resource.name}
                        onClick={() => handleItemClick(resource)}
                        className="p-4 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-all"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-slate-800">{resource.name}</h3>
                          <ChevronRight className="w-5 h-5 text-slate-400" />
                        </div>
                        <p className="text-sm text-slate-600">{resource.modules.length} modules</p>
                      </div>
                    ))}
                  </div>
                )}

                {currentView === 'modules' && (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {currentData.map((module) => (
                      <div
                        key={module.name}
                        onClick={() => handleItemClick(module)}
                        className="p-4 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-all"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-slate-800">{module.name}</h3>
                          <ChevronRight className="w-5 h-5 text-slate-400" />
                        </div>
                        <p className="text-sm text-slate-600">{module.sessions.length} sessions</p>
                      </div>
                    ))}
                  </div>
                )}

                {currentView === 'sessions' && (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {currentData.map((session) => {
                      // Find the session progress in myProgress
                      const resourceName = navigationPath[0]?.name;
                      const moduleName = navigationPath[1]?.name;
                      const resourceProgress = myProgress.find(r => r.name === resourceName);
                      const moduleProgress = resourceProgress?.modules.find(m => m.name === moduleName);
                      const sessionProgress = moduleProgress?.sessions.find(s => s.name === session.name);
                      
                      return (
                        <div
                          key={session.name}
                          className={`p-4 rounded-lg border transition-all ${
                            sessionProgress?.completed
                              ? 'bg-green-50 border-green-200'
                              : 'bg-white border-slate-200 hover:border-blue-300'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              {session.type === 'lab' ? (
                                <FlaskConical className="w-5 h-5 text-orange-600" />
                              ) : (
                                <Play className="w-5 h-5 text-blue-600" />
                              )}
                              <span className={`font-medium ${
                                sessionProgress?.completed ? 'text-green-800' : 'text-slate-700'
                              }`}>
                                {session.name}
                              </span>
                            </div>
                            <button
                              onClick={() => updateProgress(
                                resourceName, 
                                moduleName, 
                                session.name, 
                                !sessionProgress?.completed
                              )}
                              className={`p-1.5 rounded-full transition-colors ${
                                sessionProgress?.completed
                                  ? 'text-green-600 hover:bg-green-100'
                                  : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'
                              }`}
                            >
                              {sessionProgress?.completed ? (
                                <CheckCircle2 className="w-6 h-6" />
                              ) : (
                                <Circle className="w-6 h-6" />
                              )}
                            </button>
                          </div>
                          {sessionProgress?.completed && sessionProgress?.completed_at && (
                            <div className="text-xs text-green-600">
                              Hoàn thành: {new Date(sessionProgress.completed_at).toLocaleDateString('vi-VN')}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {navigationPath.length > 0 && (
                  <div className="mt-6 pt-4 border-t border-slate-200">
                    <Button
                      variant="outline"
                      onClick={() => handleNavigation(navigationPath.slice(0, -1))}
                      className="flex items-center gap-2"
                    >
                      <ArrowLeft className="w-4 h-4" />
                      Quay lại
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notes Tab */}
          <TabsContent value="notes" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-800">Ghi chú tiến độ</h2>
              <Dialog open={isNoteDialogOpen} onOpenChange={setIsNoteDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Tạo ghi chú
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>
                      {editingNote ? 'Chỉnh sửa ghi chú' : 'Tạo ghi chú mới'}
                    </DialogTitle>
                    <DialogDescription>
                      {editingNote ? 'Cập nhật nội dung ghi chú của bạn' : 'Tạo ghi chú về tiến độ học tập'}
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleNoteSubmit} className="space-y-4">
                    {!editingNote && (
                      <>
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-slate-700">Resource</label>
                          <select
                            value={noteForm.resource}
                            onChange={(e) => setNoteForm({ ...noteForm, resource: e.target.value, module: '', session: '' })}
                            className="w-full p-2 border border-slate-200 rounded-md focus:border-blue-500 focus:ring-blue-500"
                            required
                          >
                            <option value="">Chọn resource</option>
                            {structure.resources.map((resource) => (
                              <option key={resource.name} value={resource.name}>{resource.name}</option>
                            ))}
                          </select>
                        </div>
                        
                        {noteForm.resource && (
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Module</label>
                            <select
                              value={noteForm.module}
                              onChange={(e) => setNoteForm({ ...noteForm, module: e.target.value, session: '' })}
                              className="w-full p-2 border border-slate-200 rounded-md focus:border-blue-500 focus:ring-blue-500"
                              required
                            >
                              <option value="">Chọn module</option>
                              {structure.resources
                                .find(r => r.name === noteForm.resource)?.modules
                                .map((module) => (
                                  <option key={module.name} value={module.name}>{module.name}</option>
                                )) || []}
                            </select>
                          </div>
                        )}
                        
                        {noteForm.module && (
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Session</label>
                            <select
                              value={noteForm.session}
                              onChange={(e) => setNoteForm({ ...noteForm, session: e.target.value })}
                              className="w-full p-2 border border-slate-200 rounded-md focus:border-blue-500 focus:ring-blue-500"
                              required
                            >
                              <option value="">Chọn session</option>
                              {structure.resources
                                .find(r => r.name === noteForm.resource)?.modules
                                .find(m => m.name === noteForm.module)?.sessions
                                .map((session) => (
                                  <option key={session.name} value={session.name}>{session.name}</option>
                                )) || []}
                            </select>
                          </div>
                        )}
                      </>
                    )}
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Nội dung</label>
                      <Textarea
                        value={noteForm.content}
                        onChange={(e) => setNoteForm({ ...noteForm, content: e.target.value })}
                        placeholder="Nhập nội dung ghi chú..."
                        rows={4}
                        className="border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                        {editingNote ? 'Cập nhật' : 'Tạo ghi chú'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setIsNoteDialogOpen(false);
                          setNoteForm({ resource: '', module: '', session: '', content: '' });
                          setEditingNote(null);
                        }}
                      >
                        Hủy
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid gap-4">
              {notes.length === 0 ? (
                <Card className="shadow-sm border-slate-200">
                  <CardContent className="p-8 text-center">
                    <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">Chưa có ghi chú nào</p>
                  </CardContent>
                </Card>
              ) : (
                notes.map((note) => (
                  <Card key={note.id} className="shadow-sm border-slate-200">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar className="w-8 h-8">
                            <AvatarFallback className="bg-slate-100 text-slate-600 text-sm">
                              {note.user_full_name.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium text-slate-800">{note.user_full_name}</div>
                            <div className="text-sm text-slate-500">@{note.username}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex gap-1">
                            <Badge variant="secondary" className="bg-blue-50 text-blue-700 text-xs">
                              {note.resource}
                            </Badge>
                            <Badge variant="secondary" className="bg-green-50 text-green-700 text-xs">
                              {note.module}
                            </Badge>
                            <Badge variant="secondary" className="bg-orange-50 text-orange-700 text-xs">
                              {note.session}
                            </Badge>
                          </div>
                          {note.username === user?.username && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => {
                                  setEditingNote(note);
                                  setNoteForm({ 
                                    resource: note.resource, 
                                    module: note.module, 
                                    session: note.session, 
                                    content: note.content 
                                  });
                                  setIsNoteDialogOpen(true);
                                }}
                                className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteNote(note.id)}
                                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-slate-700 whitespace-pre-wrap">{note.content}</p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                        <span>Tạo: {new Date(note.created_at).toLocaleString('vi-VN')}</span>
                        {note.updated_at && (
                          <span>• Sửa: {new Date(note.updated_at).toLocaleString('vi-VN')}</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

// Protected Route Component (unchanged)
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Đang tải...</p>
        </div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;