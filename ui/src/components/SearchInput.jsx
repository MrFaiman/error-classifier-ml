import React from 'react';
import {
    Box,
    Button,
    CircularProgress,
    FormControl,
    FormControlLabel,
    Grid,
    InputLabel,
    MenuItem,
    Select,
    Switch,
    TextField,
    Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

function SearchInput({
    errorInput,
    onErrorInputChange,
    method,
    onMethodChange,
    multiSearch,
    onMultiSearchChange,
    onSearch,
    isSearching,
}) {
    return (
        <Grid container spacing={3}>
            <Grid item xs={12}>
                <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Error Message"
                    placeholder="Enter the error message or log snippet..."
                    value={errorInput}
                    onChange={(e) => onErrorInputChange(e.target.value)}
                    variant="outlined"
                />
            </Grid>

            <Grid item xs={12}>
                <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={isSearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                    onClick={onSearch}
                    disabled={isSearching || !errorInput.trim()}
                >
                    {isSearching ? 'Classifying...' : 'Classify Error'}
                </Button>
            </Grid>
        </Grid>
    );
}

export default SearchInput;
