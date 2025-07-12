const API_BASE = 'http://localhost:5001/api';

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (e) {
          // If parsing JSON fails, use the default error message
        }
        throw new Error(errorMessage);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth methods
  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout() {
    return this.request('/auth/logout', { method: 'POST' });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  async updateProfile(profileData) {
    return this.request('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async changePassword(currentPassword, newPassword) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      }),
    });
  }

  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);

    return this.request('/auth/upload-avatar', {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });
  }

  async removeAvatar() {
    return this.request('/auth/remove-avatar', {
      method: 'DELETE',
    });
  }

  // Account methods
  async getAccounts() {
    return this.request('/accounts');
  }

  async getAccount(accountId) {
    return this.request(`/accounts/${accountId}`);
  }

  async createAccount(accountData) {
    return this.request('/accounts', {
      method: 'POST',
      body: JSON.stringify(accountData),
    });
  }

  async updateAccount(accountId, accountData) {
    return this.request(`/accounts/${accountId}`, {
      method: 'PUT',
      body: JSON.stringify(accountData),
    });
  }

  async deleteAccount(accountId) {
    return this.request(`/accounts/${accountId}`, {
      method: 'DELETE',
    });
  }

  // Transaction methods
  async getTransactions(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/transactions?${queryString}`);
  }

  async uploadTransactions(file, accountId, format = 'generic') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', accountId);
    formData.append('format', format);

    return this.request('/transactions/upload', {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });
  }

  async updateTransaction(transactionId, updates) {
    return this.request(`/transactions/${transactionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteTransaction(transactionId) {
    return this.request(`/transactions/${transactionId}`, {
      method: 'DELETE',
    });
  }

  // Category methods
  async getCategories() {
    return this.request('/categories');
  }

  async createCategory(categoryData) {
    return this.request('/categories', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    });
  }

  // CSV Upload methods
  async uploadCsvFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/csv/upload', {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });
  }

  async validateCsvMapping(mappings) {
    return this.request('/csv/validate-mapping', {
      method: 'POST',
      body: JSON.stringify({ mappings }),
    });
  }

  async previewCsvImport(mappings, accountId) {
    return this.request('/csv/preview', {
      method: 'POST',
      body: JSON.stringify({ mappings, account_id: accountId }),
    });
  }

  async confirmCsvImport() {
    return this.request('/csv/confirm', {
      method: 'POST',
    });
  }

  async cancelCsvUpload() {
    return this.request('/csv/cancel', {
      method: 'POST',
    });
  }

  async getCsvAccounts() {
    return this.request('/csv/accounts');
  }

  // Budget methods
  async getBudgets() {
    return this.request('/budgets');
  }

  async getBudget(budgetId) {
    return this.request(`/budgets/${budgetId}`);
  }

  async createBudget(budgetData) {
    return this.request('/budgets', {
      method: 'POST',
      body: JSON.stringify(budgetData),
    });
  }

  async updateBudget(budgetId, budgetData) {
    return this.request(`/budgets/${budgetId}`, {
      method: 'PUT',
      body: JSON.stringify(budgetData),
    });
  }

  async deleteBudget(budgetId) {
    return this.request(`/budgets/${budgetId}`, {
      method: 'DELETE',
    });
  }

  async getBudgetPerformance(budgetId) {
    return this.request(`/budgets/${budgetId}/performance`);
  }

  async getAvailableMonths() {
    return this.request('/budgets/available-months');
  }

  async getMonthlyAnalysis(year, month) {
    return this.request(`/budgets/monthly-analysis/${year}/${month}`);
  }

  async detectRecurringTransactions() {
    return this.request('/budgets/detect-recurring', {
      method: 'POST',
    });
  }

  async getRecurringPatterns() {
    return this.request('/budgets/recurring-patterns');
  }

  async getBudgetAlerts() {
    return this.request('/budgets/alerts');
  }
}

// Global API client instance
window.api = new ApiClient();

// Global utility functions
window.showUploadModal = function() {
  document.getElementById('file-upload-modal').classList.remove('hidden');
  loadAccountsForUpload();
};

window.closeUploadModal = function() {
  document.getElementById('file-upload-modal').classList.add('hidden');
  document.getElementById('upload-form').reset();
  document.getElementById('upload-progress').classList.add('hidden');
};

window.uploadTransactions = function(accountId) {
  window.showUploadModal();
  if (accountId) {
    document.getElementById('account-select').value = accountId;
  }
};

window.viewTransactions = function(accountId) {
  window.location.href = `/transactions?account_id=${accountId}`;
};

window.updateTransactionCategory = async function(transactionId, categoryId) {
  try {
    await window.api.updateTransaction(transactionId, { category_id: categoryId });
    // Show success message or refresh data
  } catch (error) {
    console.error('Failed to update category:', error);
    alert('Failed to update category');
  }
};

async function loadAccountsForUpload() {
  try {
    const accounts = await window.api.getAccounts();
    const select = document.getElementById('account-select');
    select.innerHTML = '<option value="">Choose an account...</option>';
    
    accounts.forEach(account => {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = `${account.name} (${account.institution || 'Unknown'})`;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Failed to load accounts:', error);
  }
}

// File upload handling
document.addEventListener('DOMContentLoaded', function() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const uploadForm = document.getElementById('upload-form');
  const progressContainer = document.getElementById('upload-progress');
  const progressBar = document.getElementById('progress-bar');

  if (dropzone && fileInput) {
    // Click to browse
    dropzone.addEventListener('click', () => fileInput.click());

    // Drag and drop
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('border-blue-400', 'bg-blue-50');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('border-blue-400', 'bg-blue-50');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-blue-400', 'bg-blue-50');
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateDropzoneText(files[0]);
      }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        updateDropzoneText(e.target.files[0]);
      }
    });
  }

  // Form submission
  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const file = fileInput.files[0];
      const accountId = document.getElementById('account-select').value;
      const format = document.getElementById('format-select').value;

      if (!file || !accountId) {
        alert('Please select a file and account');
        return;
      }

      try {
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';

        // Simulate progress (in real app, you'd track actual upload progress)
        const progressInterval = setInterval(() => {
          const currentWidth = parseInt(progressBar.style.width) || 0;
          if (currentWidth < 90) {
            progressBar.style.width = (currentWidth + 10) + '%';
          }
        }, 200);

        const result = await window.api.uploadTransactions(file, accountId, format);
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';

        if (result.success) {
          alert(`Upload successful! Processed: ${result.processed}, Duplicates: ${result.duplicates}, Errors: ${result.errors}`);
          window.closeUploadModal();
          // Refresh the page or update data
          window.location.reload();
        } else {
          alert(`Upload failed: ${result.error}`);
        }
      } catch (error) {
        console.error('Upload failed:', error);
        alert('Upload failed. Please try again.');
      } finally {
        progressContainer.classList.add('hidden');
      }
    });
  }

  function updateDropzoneText(file) {
    const dropzone = document.getElementById('dropzone');
    if (dropzone) {
      dropzone.innerHTML = `
        <p class="text-gray-600">Selected: ${file.name}</p>
        <p class="text-sm text-gray-400 mt-2">Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
      `;
    }
  }
});