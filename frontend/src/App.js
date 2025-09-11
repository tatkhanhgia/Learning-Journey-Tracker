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
  User
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
      
      toast.success(`Chào mừng ${user_info.full_name}!`);
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

// Login Component
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogging, setIsLogging] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(''); // Clear previous errors
    
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
              
              {/* Error Message Display */}
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

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [allProgress, setAllProgress] = useState([]);
  const [myProgress, setMyProgress] = useState([]);
  const [notes, setNotes] = useState([]);
  const [levels, setLevels] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Note dialog states
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [noteForm, setNoteForm] = useState({ level: '', content: '' });
  const [editingNote, setEditingNote] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [progressRes, myProgressRes, notesRes, levelsRes, usersRes] = await Promise.all([
        axios.get(`${API}/progress`),
        axios.get(`${API}/progress/me`),
        axios.get(`${API}/notes`),
        axios.get(`${API}/config/levels`),
        axios.get(`${API}/config/users`)
      ]);

      setAllProgress(progressRes.data.progress);
      setMyProgress(myProgressRes.data.progress);
      setNotes(notesRes.data.notes);
      setLevels(levelsRes.data.levels);
      setUsers(usersRes.data.users);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  const updateProgress = async (level, completed) => {
    try {
      await axios.post(`${API}/progress`, { level, completed });
      await fetchData();
      toast.success(completed ? 'Đã đánh dấu hoàn thành' : 'Đã hủy đánh dấu hoàn thành');
    } catch (error) {
      console.error('Failed to update progress:', error);
      toast.error('Không thể cập nhật tiến độ');
    }
  };

  const handleNoteSubmit = async (e) => {
    e.preventDefault();
    if (!noteForm.level || !noteForm.content.trim()) {
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
      setNoteForm({ level: '', content: '' });
      setEditingNote(null);
      await fetchData();
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
      await fetchData();
    } catch (error) {
      console.error('Failed to delete note:', error);
      toast.error('Không thể xóa ghi chú');
    }
  };

  const getProgressPercentage = (userProgress) => {
    const completedLevels = userProgress.levels.filter(level => level.completed).length;
    return levels.length > 0 ? Math.round((completedLevels / levels.length) * 100) : 0;
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

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6">
              <h2 className="text-2xl font-semibold text-slate-800">Tiến độ của tất cả thành viên</h2>
              
              <div className="grid gap-4">
                {allProgress.map((userProgress) => (
                  <Card key={userProgress.username} className="shadow-sm border-slate-200">
                    <CardHeader className="pb-4">
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
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600">
                            {getProgressPercentage(userProgress)}%
                          </div>
                          <div className="text-sm text-slate-500">Hoàn thành</div>
                        </div>
                      </div>
                      <Progress 
                        value={getProgressPercentage(userProgress)} 
                        className="mt-3"
                      />
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {userProgress.levels.map((level) => (
                          <div
                            key={`${userProgress.username}-${level.level}`}
                            className={`flex items-center gap-2 p-3 rounded-lg border ${
                              level.completed
                                ? 'bg-green-50 border-green-200'
                                : 'bg-slate-50 border-slate-200'
                            }`}
                          >
                            {level.completed ? (
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            ) : (
                              <Circle className="w-5 h-5 text-slate-400" />
                            )}
                            <span className={`text-sm font-medium ${
                              level.completed ? 'text-green-800' : 'text-slate-600'
                            }`}>
                              {level.level}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* My Progress Tab */}
          <TabsContent value="my-progress" className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-800">Tiến độ của tôi</h2>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">
                  {myProgress.length > 0 ? Math.round((myProgress.filter(p => p.completed).length / myProgress.length) * 100) : 0}%
                </div>
                <div className="text-sm text-slate-500">Hoàn thành</div>
              </div>
            </div>

            <Card className="shadow-sm border-slate-200">
              <CardContent className="p-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {myProgress.map((level) => (
                    <div
                      key={level.level}
                      className={`p-4 rounded-lg border transition-all ${
                        level.completed
                          ? 'bg-green-50 border-green-200'
                          : 'bg-white border-slate-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className={`font-medium ${
                          level.completed ? 'text-green-800' : 'text-slate-700'
                        }`}>
                          {level.level}
                        </span>
                        <button
                          onClick={() => updateProgress(level.level, !level.completed)}
                          className={`p-1.5 rounded-full transition-colors ${
                            level.completed
                              ? 'text-green-600 hover:bg-green-100'
                              : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'
                          }`}
                        >
                          {level.completed ? (
                            <CheckCircle2 className="w-6 h-6" />
                          ) : (
                            <Circle className="w-6 h-6" />
                          )}
                        </button>
                      </div>
                      {level.completed && level.completed_at && (
                        <div className="text-xs text-green-600">
                          Hoàn thành: {new Date(level.completed_at).toLocaleDateString('vi-VN')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
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
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700">Module</label>
                        <select
                          value={noteForm.level}
                          onChange={(e) => setNoteForm({ ...noteForm, level: e.target.value })}
                          className="w-full p-2 border border-slate-200 rounded-md focus:border-blue-500 focus:ring-blue-500"
                          required
                        >
                          <option value="">Chọn module</option>
                          {levels.map((level) => (
                            <option key={level} value={level}>{level}</option>
                          ))}
                        </select>
                      </div>
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
                          setNoteForm({ level: '', content: '' });
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
                          <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                            {note.level}
                          </Badge>
                          {note.username === user?.username && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => {
                                  setEditingNote(note);
                                  setNoteForm({ level: note.level, content: note.content });
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

// Protected Route Component
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