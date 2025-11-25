import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

// Classification API
export const classifyError = async (data) => {
    const response = await api.post('/classify', data);
    return response.data;
};

export const teachCorrection = async (data) => {
    const response = await api.post('/teach-correction', data);
    return response.data;
};

// Documentation API
export const getDocs = async () => {
    const response = await api.get('/docs');
    return response.data;
};

export const createDoc = async (data) => {
    const response = await api.post('/docs', data);
    return response.data;
};

export const updateDoc = async ({ id, ...data }) => {
    const response = await api.put(`/docs/${id}`, data);
    return response.data;
};

export const deleteDoc = async (id) => {
    const response = await api.delete(`/docs/${id}`);
    return response.data;
};

// Get documentation file content
export const getDocContent = async (docPath) => {
    const response = await api.get('/doc-content', {
        params: { path: docPath },
    });
    return response.data;
};

// Dataset API
export const getDataset = async () => {
    const response = await api.get('/dataset');
    return response.data;
};

export const createDatasetRecord = async (data) => {
    const response = await api.post('/dataset', data);
    return response.data;
};

export const updateDatasetRecord = async ({ id, ...data }) => {
    const response = await api.put(`/dataset/${id}`, data);
    return response.data;
};

export const deleteDatasetRecord = async (id) => {
    const response = await api.delete(`/dataset/${id}`);
    return response.data;
};

// System API
export const updateKB = async () => {
    const response = await api.post('/update-kb');
    return response.data;
};

export const getStatus = async () => {
    const response = await api.get('/status');
    return response.data;
};

export const getSearchEnginesComparison = async () => {
    const response = await api.get('/search-engines-comparison');
    return response.data;
};
