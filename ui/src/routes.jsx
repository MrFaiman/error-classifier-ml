import React from 'react';
import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router';
import Box from '@mui/material/Box';
import Navigation from './components/Navigation';
import SearchPage from './pages/SearchPage';
import ManageDocsPage from './pages/ManageDocsPage';
import ManageDatasetPage from './pages/ManageDatasetPage';
import StatusPage from './pages/StatusPage';

// Root route with layout
const rootRoute = createRootRoute({
    component: () => (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navigation />
            <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                {/* This is where child routes will render */}
                <Outlet />
            </Box>
        </Box>
    ),
});

// Define individual routes
const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: SearchPage,
});

const docsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/docs',
    component: ManageDocsPage,
});

const datasetRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/dataset',
    component: ManageDatasetPage,
});

const statusRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/status',
    component: StatusPage,
});

// Create the route tree
const routeTree = rootRoute.addChildren([
    indexRoute,
    docsRoute,
    datasetRoute,
    statusRoute,
]);

// Create and export the router
export const router = createRouter({ routeTree });
