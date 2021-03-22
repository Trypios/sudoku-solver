
class ConflictError(Exception):
    pass


class Cell:
    """ One of the 81 sudoku cells. See Cell.__init__() for info. """

    def __init__(self, r_pos, c_pos, value=0):
        """
        r_pos: row position (vertical)
        c_pos: column position (horizontal)
        key: concatenated coordinates
        value: number 1-9, 0 if unsolved
        possib: a set of possible numbers for value (1-9)
        """
        self.r_pos = r_pos
        self.c_pos = c_pos
        self.key = f'{r_pos}{c_pos}'
        self.value = value
        self.possib = {v + 1 for v in range(9) if v + 1 != value}
    
    def __str__(self):
        """ Return value of cell, or a dot if unknown """
        return str(self.value) if self.value != 0 else '.'
    
    def __eq__(self, other):
        """ Compare cells based on value """
        if isinstance(other, int):
            return self.value == other
        return self.value != 0 and self.value == other.value
    
    def __hash__(self):
        """ Return a hash of the concatenated coordinates """
        return hash(self.key)
    
    def is_solved(self):
        """ Return true if cell contains a value other than 0 """
        return self.value != 0
    
    def reduce_possibilities(self, group):
        """
        Take a set of values (group arg) and remove possibilities if they exist in that group.
        Establish value if only one possibility is left. Returns true if any changes have been made, 
        false if no possibilities removed
        """
        is_reduced = False
        for other_value in group:
            if self == other_value:
                raise ConflictError
            if other_value in self.possib:
                self.possib.remove(other_value)
                is_reduced = True
            if len(self.possib) == 1:
                self.set_value(self.possib.pop(), True)
                break
        return is_reduced
    
    def set_value(self, value, certainty=False):
        """ Set the cell's value and if certain for that value: eliminate all possibilities left """
        self.value = value
        if certainty:
            self.possib.clear()


class Sudoku:
    """
    Takes a list of 81 integers to initialize.
    It can be solved whether normal or special sudoku in any difficulty, by brute force backtracking.
    Special sudoku rules here: https://www.youtube.com/watch?v=hAyZ9K2EBF0
    """

    def __init__(self, grid):
        """
        Initialize sudoku from a list of 81 integers,
        where 0 means an unsolved cell
        """
        self.grid = self.__parse_grid(grid)
        self.unsolved_cells = [cell for row in self.grid for cell in row if not cell.is_solved()]

    def __str__(self):
        """ Return sudoku grid in a printable format """
        line = f"{'-' * 25}\n"
        result = line
        for r in range(9):
            result += '| '
            for c in range(9):
                result += f'{self.grid[r][c]} '
                if c in [2, 5, 8]:
                    result += '| '
            result += '\n'
            if r in [2, 5, 8]:
                result += line
        return result

    def __parse_grid(self, grid):
        """ Parse a list of numbers to list of cells. Helper of __init__(). """
        result = []
        i = 0
        for r in range(9):
            row = []
            for c in range(9):
                cell = Cell(r, c, grid[i])
                row.append(cell)
                i += 1
            result.append(row)
        return result
    
    def __all_solved(self):
        """ Return true if all 81 cells are solved, else false """
        return len(self.unsolved_cells) == 0

    def __constraining_values(self, target, special=False):
        """ Return a set of values from same row, column and square of the target cell """
        r_pos = target.r_pos
        c_pos = target.c_pos
        # row constraining values
        row = {cell.value for cell in self.grid[r_pos] 
                    if cell is not target and cell.is_solved()}
        # column constraining values
        column = {self.grid[r][c_pos].value for r in range(9) 
                                    if r != r_pos and self.grid[r][c_pos].is_solved()}
        row_start, col_start = r_pos // 3 * 3, c_pos // 3 * 3
        # square constraining values
        square = {self.grid[r][c].value for r in range(row_start, row_start + 3) 
                                    for c in range(col_start, col_start + 3) 
                                        if not (r == r_pos and c == c_pos) 
                                        and self.grid[r][c].is_solved()}
        group = row.union(column).union(square)
        if special:
            group = group.union(self.__special_constraining_values(target))
        return group

    def __special_constraining_values(self, target):
        """   """
        r_pos = target.r_pos
        c_pos = target.c_pos
        # knights constraining values
        knights = {self.grid[r_pos + r][c_pos + c].value for r in [-2, -1, 1, 2] 
                                                        for c in [-2, -1, 1, 2] 
                                                if 0 <= r_pos + r <= 8 and 
                                                0 <= c_pos + c <= 8 and 
                                                abs(r) != abs(c) and 
                                                self.grid[r_pos + r][c_pos + c].is_solved()}
        group = knights
        if r_pos == c_pos:
            # main diagonal constraining values
            main_diag = {self.grid[i][i].value for i in range(9) 
                                                if self.grid[i][i].is_solved()}
            group = group.union(main_diag)
        if sum([r_pos, c_pos]) == 8:
            # side diagonal constraining values
            side_diag = {self.grid[i][8 - i].value for i in range(9) 
                                                if self.grid[i][8 - i].is_solved()}
            group = group.union(side_diag)
        return group

    def __check_cell_possib(self, target, possib_value, special=False):
        """
        Check if possible value is correct for target at this given moment
        based on row, column and square. If special, it also checks for magic square,
        knights moves and big diagonals. This method is used for brute force,
        hence that possible value could prove incorrect at a later iteration.
        """
        group = self.__constraining_values(target, special)
        is_possible = possib_value not in group
        return is_possible
    
    def __reduce_cell(self, target, certainty=False, special=False):
        """
        Helper of __reduce_cells().
        Check row, column and square of target cell and reduce its possibilities
        """
        if not target.is_solved():
            group = self.__constraining_values(target, special)
            return target.reduce_possibilities(group)

    def __reduce_cells(self, certainty=False, special=False):
        """ Reduce each cell's possible values """
        reducing = True
        while reducing:
            if self.__all_solved():
                break
            reducing = []
            for cell in self.unsolved_cells:
                reducing.append(self.__reduce_cell(cell, certainty, special))
                if cell.is_solved():
                    self.unsolved_cells.remove(cell)
            reducing = any(reducing)
    
    def __get_mid_square(self):
        """ Return the central 3x3 square as a 2D grid"""
        result = []
        for row in self.grid[3:6]:
            result.append([cell for cell in row[3:6]])
        return result

    def __check_magic_square_state(self):
        """
        Check if central square does not break the 'magic' properties
        (rows, columns, main diag and side diagonal must each have a sum = 15)
        """
        mid_square = self.__get_mid_square()
        # check 3 rows
        for row in mid_square:
            row_values = [cell.value for cell in row if cell.is_solved()]
            if len(row_values) == 3 and sum(row_values) != 15:
                return False
        # check 3 columns
        for col in range(3):
            col_values = [mid_square[row][col].value for row in range(3) if mid_square[row][col].is_solved()]
            if len(col_values) == 3 and sum(col_values) != 15:
                return False
        # check main diagonal
        mdiag_values = [mid_square[i][i].value for i in range(3) if mid_square[i][i].is_solved()]
        if len(mdiag_values) == 3 and sum(mdiag_values) != 15:
            return False
        # check side diagonal
        sdiag_values = [mid_square[i][2 - i].value for i in range(3) if mid_square[i][2 - i].is_solved()]
        if len(sdiag_values) == 3 and sum(sdiag_values) != 15:
            return False
        # passed all tests
        return True

    def __solve_magic_square(self):
        """
        Solve the central 3x3 box being a magic square
        (sum of each row, column and diagonal = 15)
        """
        mid_square_list = [cell for row in self.__get_mid_square() for cell in row if not cell.is_solved()]
        self.__brute_force_magic_square(mid_square_list)
    
    def __brute_force_magic_square(self, mid_square):
        """ Docstring here """
        try:
            cell = mid_square.pop(0)
        except IndexError:
            return True

        for value in cell.possib:
            if self.__check_magic_square_state() and self.__check_cell_possib(cell, value, special=True):
                cell.set_value(value)
                if self.__brute_force_magic_square(mid_square):
                    return True
                cell.value = 0  # undo change
        mid_square.insert(0, cell)  # backtrack
        return False
    
    def __brute_force(self, special=False):
        """ Try every value and backtrack when solution fails """
        try:
            cell = self.unsolved_cells.pop(0)
        except IndexError:
            return True

        for value in cell.possib:
            if self.__check_cell_possib(cell, value, special):
                cell.set_value(value)
                if self.__brute_force(special):
                    return True
                cell.value = 0  # undo change
        self.unsolved_cells.insert(0, cell)  # backtrack
        return False
    
    def grid_to_list(self):
        """ Return a list of numbers, being the cell values from the grid """
        lst = []
        for row in self.grid:
            for cell in row:
                lst.append(cell.value)
        return lst
    
    def solve(self, special=False):
        """ Solve the sudoku whether normal or special """
        self.__reduce_cells(certainty=True, special=special)
        if special:
            self.__solve_magic_square()
            self.__reduce_cells(certainty=True, special=True)
        self.__brute_force(special)
    

if __name__ == "__main__":
    unsolved = [0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                3, 8, 4, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 2]
    solution = [8, 4, 3, 5, 6, 7, 2, 1, 9,
                2, 7, 5, 9, 1, 3, 8, 4, 6,
                6, 1, 9, 4, 2, 8, 3, 7, 5,
                3, 8, 4, 6, 7, 2, 9, 5, 1,
                7, 2, 6, 1, 5, 9, 4, 8, 3,
                9, 5, 1, 8, 3, 4, 6, 2, 7,
                5, 3, 7, 2, 8, 6, 1, 9, 4,
                4, 6, 2, 7, 9, 1, 5, 3, 8,
                1, 9, 8, 3, 4, 5, 7, 6, 2]
    sudoku = Sudoku(unsolved)
    print(sudoku)
    sudoku.solve(special=True)
    print(sudoku)
