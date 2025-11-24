import React from 'react';
import { Link, useRouterState } from '@tanstack/react-router';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import SearchIcon from '@mui/icons-material/Search';
import DescriptionIcon from '@mui/icons-material/Description';
import StorageIcon from '@mui/icons-material/Storage';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';

function Navigation() {
    const routerState = useRouterState();
    const currentPath = routerState.location.pathname;

    const navItems = [
        { path: '/', label: 'Search', icon: <SearchIcon /> },
        { path: '/docs', label: 'Manage Docs', icon: <DescriptionIcon /> },
        { path: '/dataset', label: 'Manage Dataset', icon: <StorageIcon /> },
        { path: '/status', label: 'Status', icon: <MonitorHeartIcon /> },
    ];

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Error Classifier ML
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    {navItems.map((item) => (
                        <Button
                            key={item.path}
                            color="inherit"
                            component={Link}
                            to={item.path}
                            startIcon={item.icon}
                            sx={{
                                borderBottom: currentPath === item.path ? '2px solid white' : 'none',
                            }}
                        >
                            {item.label}
                        </Button>
                    ))}
                </Box>
            </Toolbar>
        </AppBar>
    );
}

export default Navigation;
