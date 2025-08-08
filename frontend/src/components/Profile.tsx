// Profile.tsx - Complete profile page with edit functionality
import React, { useState, useEffect } from 'react';
import { ArrowLeft, Edit, Save, X, Phone, MapPin, Calendar, Mail, User, Settings, LogOut, Trash2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { updateProfile, deleteUser, updatePassword } from 'firebase/auth';
import { toast } from '@/hooks/use-toast';

interface ProfileData {
  firstName: string;
  lastName: string;
  email: string;
  username: string;
  phone: string;
  location: string;
  memberSince: string;
}

const Profile: React.FC = () => {
  const { currentUser, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData>({
    firstName: '',
    lastName: '',
    email: '',
    username: '',
    phone: '',
    location: '',
    memberSince: ''
  });
  const [originalData, setOriginalData] = useState<ProfileData>({
    firstName: '',
    lastName: '',
    email: '',
    username: '',
    phone: '',
    location: '',
    memberSince: ''
  });

  // Initialize profile data from Firebase user
  useEffect(() => {
    if (currentUser) {
      const displayName = currentUser.displayName || '';
      const [firstName = '', lastName = ''] = displayName.split(' ');
      
      const data = {
        firstName,
        lastName,
        email: currentUser.email || '',
        username: currentUser.email?.split('@')[0] || '',
        phone: currentUser.phoneNumber || '',
        location: '',
        memberSince: currentUser.metadata.creationTime 
          ? new Date(currentUser.metadata.creationTime).toLocaleDateString('en-US', { 
              month: 'long', 
              year: 'numeric' 
            })
          : 'Recently'
      };
      
      setProfileData(data);
      setOriginalData(data);
    }
  }, [currentUser]);

  // Handle input changes
  const handleInputChange = (field: keyof ProfileData, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Save profile changes
  const handleSaveProfile = async () => {
    if (!currentUser) return;

    setLoading(true);
    try {
      // Update display name in Firebase
      const fullName = `${profileData.firstName} ${profileData.lastName}`.trim();
      await updateProfile(currentUser, {
        displayName: fullName || profileData.firstName
      });

      setOriginalData(profileData);
      setIsEditing(false);
      
      toast({
        title: "Profile Updated",
        description: "Your profile has been successfully updated.",
      });
    } catch (error) {
      console.error('Profile update error:', error);
      toast({
        title: "Update Failed",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Cancel editing
  const handleCancelEdit = () => {
    setProfileData(originalData);
    setIsEditing(false);
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out.",
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Handle account deletion
  const handleDeleteAccount = async () => {
    if (!currentUser) return;

    const confirmed = window.confirm(
      'Are you sure you want to delete your account? This action cannot be undone and will permanently delete all your data.'
    );

    if (!confirmed) return;

    try {
      setLoading(true);
      await deleteUser(currentUser);
      
      toast({
        title: "Account Deleted",
        description: "Your account has been permanently deleted.",
      });
    } catch (error: any) {
      console.error('Delete account error:', error);
      
      if (error.code === 'auth/requires-recent-login') {
        toast({
          title: "Re-authentication Required",
          description: "Please log out and log back in before deleting your account.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Deletion Failed",
          description: "Failed to delete account. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Navigate back function (you'll implement this with your router)
  const handleGoBack = () => {
    // TODO: Implement navigation back to main app
    // Example: navigate(-1) or navigate('/')
    window.history.back();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={handleGoBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
            </div>
            
            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <button
                    onClick={handleCancelEdit}
                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    disabled={loading}
                  >
                    <X className="w-4 h-4 mr-2 inline" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveProfile}
                    className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors disabled:bg-blue-400"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2 inline-block"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2 inline" />
                        Save
                      </>
                    )}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
                >
                  <Edit className="w-4 h-4 mr-2 inline" />
                  Edit
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {/* Profile Header */}
          <div className="px-6 py-6 border-b border-gray-200">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-center text-white text-xl font-bold">
                {profileData.firstName[0]}{profileData.lastName[0]}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Member since {profileData.memberSince}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Profile Information */}
          <div className="px-6 py-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={profileData.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    disabled={loading}
                  />
                ) : (
                  <p className="text-gray-900">{profileData.firstName || 'Not provided'}</p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={profileData.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    disabled={loading}
                  />
                ) : (
                  <p className="text-gray-900">{profileData.lastName || 'Not provided'}</p>
                )}
              </div>

              {/* Email Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-900">{profileData.email}</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Verified
                  </span>
                </div>
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Username
                </label>
                {isEditing ? (
                  <div className="flex items-center">
                    <span className="text-gray-500 mr-1">@</span>
                    <input
                      type="text"
                      value={profileData.username}
                      onChange={(e) => handleInputChange('username', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                      disabled={loading}
                    />
                  </div>
                ) : (
                  <p className="text-gray-900">@{profileData.username}</p>
                )}
              </div>
            </div>

            {/* Contact Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {/* Phone Number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                {isEditing ? (
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Phone className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                      placeholder="Enter phone number"
                      disabled={loading}
                    />
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">{profileData.phone || 'Not provided'}</span>
                  </div>
                )}
              </div>

              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
                {isEditing ? (
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <MapPin className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      value={profileData.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                      placeholder="Enter location"
                      disabled={loading}
                    />
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">{profileData.location || 'Not provided'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Account Section */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Account
            </h3>
          </div>

          <div className="px-6 py-6 space-y-4">
            {/* Delete Account */}
            <div className="flex items-center justify-between py-4 border-b border-gray-100">
              <div>
                <h4 className="text-red-600 font-medium">Delete Account</h4>
                <p className="text-sm text-gray-500">Permanently delete your account and all data</p>
              </div>
              <button
                onClick={handleDeleteAccount}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors disabled:bg-red-400 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>

            {/* Log Out */}
            <div className="flex items-center justify-between py-4">
              <div>
                <h4 className="text-gray-900 font-medium">Log Out</h4>
                <p className="text-sm text-gray-500">Sign out of your account</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Log Out
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Profile;